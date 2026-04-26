
from io import BytesIO
from pathlib import Path

import cv2
import numpy as np
import torch
from dotenv import find_dotenv, load_dotenv
from PIL import Image, ImageOps, UnidentifiedImageError

load_dotenv(find_dotenv())

from utils import (  # noqa: E402
    apply_binary_mask_for_inpainting,
    initialize_sam_model,
    initialize_yolo_model,
)

_HERE = Path(__file__).parent

working_dir = str(_HERE / "output")

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

SAM_CHECKPOINT_PATH = str(_HERE / "model" / "sam_vit_h_4b8939.pth")
SAM_MODEL_TYPE = "vit_h"
YOLO_DETECTION_MODEL_PATH = str(_HERE / "model" / "yolov10n.pt")
_MAX_IMAGE_DIMENSION = 4096
_MAX_IMAGE_PIXELS = _MAX_IMAGE_DIMENSION * _MAX_IMAGE_DIMENSION
_YOLO_IMGSZ = 640
_CAR_CLASS_ID = 2

sam_predictor = initialize_sam_model(SAM_CHECKPOINT_PATH, SAM_MODEL_TYPE, DEVICE)
yolo_detection_model = initialize_yolo_model(YOLO_DETECTION_MODEL_PATH, DEVICE)


def _yolo_imgsz(img: np.ndarray) -> int:
    """Return YOLO inference size capped at _YOLO_IMGSZ to avoid degraded detection on large uploads."""
    return min(_YOLO_IMGSZ, max(img.shape[:2]))


def _decode_image_for_cv(content: bytes) -> np.ndarray:
    """Decode uploads with EXIF orientation applied, then return OpenCV BGR pixels."""
    try:
        with Image.open(BytesIO(content)) as source_image:
            oriented = ImageOps.exif_transpose(source_image)
            rgb_image = oriented.convert("RGB")
            rgb_array = np.array(rgb_image)
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("Failed to decode image. Ensure the input is a valid image file.") from exc

    return cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)


def _validate_image_size(img: np.ndarray) -> None:
    height, width = img.shape[:2]
    if (
        width < 1
        or height < 1
        or width > _MAX_IMAGE_DIMENSION
        or height > _MAX_IMAGE_DIMENSION
        or width * height > _MAX_IMAGE_PIXELS
    ):
        raise ValueError(
            "Image dimensions are too large. "
            f"Maximum is {_MAX_IMAGE_DIMENSION}px per side and {_MAX_IMAGE_PIXELS} pixels total."
        )


def _detect_car_boxes(img: np.ndarray) -> torch.Tensor:
    results = yolo_detection_model.predict(
        img,
        classes=[_CAR_CLASS_ID],
        conf=0.25,
        imgsz=_yolo_imgsz(img),
    )
    if len(results) == 0:
        raise ValueError("No cars detected in image.")

    boxes = results[0].boxes.xyxy
    if len(boxes) == 0:
        raise ValueError("No cars detected in image.")

    return boxes


def _select_closest_car_box(boxes: torch.Tensor, image_shape: tuple[int, int]) -> torch.Tensor:
    """Approximate closest car by combining box area with lower frame position."""
    height, width = image_shape
    image_area = max(height * width, 1)

    box_widths = (boxes[:, 2] - boxes[:, 0]).clamp(min=0)
    box_heights = (boxes[:, 3] - boxes[:, 1]).clamp(min=0)
    area_score = (box_widths * box_heights) / image_area
    bottom_score = boxes[:, 3] / max(height, 1)

    best_idx = torch.argmax(area_score + (0.25 * bottom_score))
    return boxes[best_idx].unsqueeze(0)


def _segment_selected_box(img: np.ndarray, box: torch.Tensor) -> np.ndarray:
    sam_predictor.set_image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    transformed_boxes = sam_predictor.transform.apply_boxes_torch(
        box.clone().detach().to(sam_predictor.device),
        img.shape[:2],
    )

    masks, _, _ = sam_predictor.predict_torch(
        point_coords=None,
        point_labels=None,
        boxes=transformed_boxes,
        multimask_output=False,
    )
    return (masks[0, 0].cpu().numpy() * 255).astype(np.uint8)


def segment_car(content, edit_car=True, size=None, output_dir=None):
    """Segment the closest visible car from an input image."""
    if output_dir is None:
        output_dir = working_dir

    img = _decode_image_for_cv(content)
    _validate_image_size(img)

    boxes = _detect_car_boxes(img)
    selected_box = _select_closest_car_box(boxes, img.shape[:2])
    mask_np = _segment_selected_box(img, selected_box)

    return apply_binary_mask_for_inpainting(img, mask_np, output_dir, edit_car, size)
