"""
Integration tests: verify the YOLO stage detects exactly one car per reference
input image (front, back, side views of a single car).

Skipped automatically when yolo11n.pt is absent so CI never blocks on missing
model weights.  Run locally after placing the weights in car-segmentation-ms/model/.
"""
from pathlib import Path

import cv2
import pytest

_MODEL_DIR = Path(__file__).parent.parent / "model"
_INPUT_DIR = Path(__file__).parent.parent / "input"
_YOLO_MODEL = _MODEL_DIR / "yolo11n.pt"

pytestmark = pytest.mark.skipif(
    not _YOLO_MODEL.exists(),
    reason="yolo11n.pt not found in model/ — skipping integration detection tests",
)


@pytest.fixture(scope="module")
def yolo():
    from ultralytics import YOLO
    return YOLO(str(_YOLO_MODEL))


@pytest.mark.parametrize("filename", ["front.JPEG", "back.JPEG", "side.JPEG"])
def test_single_car_detected(yolo, filename):
    img = cv2.imread(str(_INPUT_DIR / filename))
    assert img is not None, f"Could not read test image: {filename}"

    results = yolo.predict(img, classes=[2], conf=0.25, imgsz=640, verbose=False)
    boxes = results[0].boxes.xyxy

    assert len(boxes) >= 1, (
        f"{filename}: no car detected — model may not have loaded correctly "
        "or confidence threshold is too high for this image"
    )
    assert len(boxes) == 1, (
        f"{filename}: expected 1 car box, got {len(boxes)} — "
        "image contains multiple cars or YOLO is producing duplicate detections"
    )
