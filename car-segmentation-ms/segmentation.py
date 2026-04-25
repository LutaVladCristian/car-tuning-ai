
from pathlib import Path

import cv2
import numpy as np
import torch
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

from utils import (  # noqa: E402
    apply_binary_mask_for_inpainting,
    initialize_sam_model,
    initialize_yolo_model,
)

# H2: Use absolute paths derived from this file's location so the service
# starts correctly regardless of the working directory.
_HERE = Path(__file__).parent

working_dir = str(_HERE / "output")

# Define device
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Constants for initialization
SAM_CHECKPOINT_PATH = str(_HERE / "model" / "sam_vit_h_4b8939.pth")
SAM_MODEL_TYPE = "vit_h"
YOLO_DETECTION_MODEL_PATH = str(_HERE / "model" / "yolov11n.pt")
_MAX_IMAGE_DIMENSION = 4096
_MAX_IMAGE_PIXELS = _MAX_IMAGE_DIMENSION * _MAX_IMAGE_DIMENSION

# Initialize models
sam_predictor = initialize_sam_model(SAM_CHECKPOINT_PATH, SAM_MODEL_TYPE, DEVICE)
yolo_detection_model = initialize_yolo_model(YOLO_DETECTION_MODEL_PATH, DEVICE)


def _native_yolo_imgsz(img: np.ndarray) -> tuple[int, int]:
    """Ask YOLO to run at the uploaded image's decoded height and width."""
    height, width = img.shape[:2]
    return height, width


def segment_car(content, inverse=True, size=None, output_dir=None):
    """Segment cars from an input image.

    Args:
        output_dir: Directory for intermediate files. Defaults to the module-level
                    working_dir. Pass a per-request temp dir to avoid race conditions
                    under concurrent load (C3).
    """
    if output_dir is None:
        output_dir = working_dir

    file_bytes = np.frombuffer(content, np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Failed to decode image. Ensure the input is a valid image file.")

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

    native_imgsz = _native_yolo_imgsz(img)

    # Try car-class detection first; fall back to any object if nothing found.
    results_yolo = yolo_detection_model.predict(
        img,
        classes=[2],
        conf=0.25,
        imgsz=native_imgsz,
    )
    boxes_yolo = results_yolo[0].boxes.xyxy if len(results_yolo) > 0 else []

    if len(boxes_yolo) == 0:
        results_yolo = yolo_detection_model.predict(img, conf=0.25, imgsz=native_imgsz)
        boxes_yolo = results_yolo[0].boxes.xyxy if len(results_yolo) > 0 else []

    # H1: raise instead of returning a dict so callers get a clean 400 response.
    if len(boxes_yolo) == 0:
        raise ValueError("No cars detected in image.")

    sam_predictor.set_image(img)

    transformed_boxes = sam_predictor.transform.apply_boxes_torch(
        boxes_yolo.clone().detach().to(sam_predictor.device),
        img.shape[:2]
    )

    car_mask = sam_predictor.predict_torch(
        point_coords=None,
        point_labels=None,
        boxes=transformed_boxes,
        multimask_output=False,
    )

    # Convert mask to numpy
    mask_np = car_mask[0][0].cpu().numpy()  # shape: (1, H, W) -> need squeeze
    mask_np = np.squeeze(mask_np)  # shape: (H, W)
    mask_np = (mask_np * 255).astype(np.uint8)

    return apply_binary_mask_for_inpainting(img, mask_np, output_dir, inverse, size)
