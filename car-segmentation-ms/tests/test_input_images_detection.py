from pathlib import Path

import cv2
import numpy as np
import pytest
from PIL import Image, ImageOps

try:
    from ultralytics import YOLO
except ImportError:  # pragma: no cover - exercised only in minimal test envs
    YOLO = None


ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / "input"
YOLO_MODEL_PATH = ROOT / "model" / "yolov10n.pt"
INPUT_IMAGES = sorted(INPUT_DIR.glob("*.JPEG"))


def _decode_display_oriented_bgr(path: Path) -> np.ndarray:
    with Image.open(path) as source_image:
        oriented = ImageOps.exif_transpose(source_image)
        rgb_array = np.array(oriented.convert("RGB"))
    return cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)


@pytest.fixture(scope="session")
def yolo_model():
    if YOLO is None:
        pytest.skip("ultralytics is not installed")
    if not YOLO_MODEL_PATH.exists():
        pytest.skip(f"YOLO model not found at {YOLO_MODEL_PATH}")
    return YOLO(str(YOLO_MODEL_PATH))


@pytest.mark.parametrize("image_path", INPUT_IMAGES, ids=lambda p: p.name)
def test_input_image_contains_detectable_car_part(yolo_model, image_path):
    if not INPUT_IMAGES:
        pytest.skip(f"No JPEG input images found in {INPUT_DIR}")

    img = _decode_display_oriented_bgr(image_path)
    height, width = img.shape[:2]
    results = yolo_model.predict(img, conf=0.25, imgsz=(height, width))
    boxes = results[0].boxes if len(results) > 0 else []

    assert len(boxes) > 0, f"No car-related object detected in {image_path.name} at {width}x{height}"
