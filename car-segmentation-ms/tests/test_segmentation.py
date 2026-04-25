import importlib
import sys
from io import BytesIO
from unittest.mock import MagicMock

import numpy as np
from PIL import Image


def _load_segmentation(monkeypatch, *, use_real_torch=False):
    if not use_real_torch:
        fake_torch = MagicMock()
        fake_torch.device.return_value = "cpu"
        monkeypatch.setitem(sys.modules, "torch", fake_torch)

    fake_utils = MagicMock()
    fake_utils.initialize_sam_model.return_value = MagicMock()
    fake_utils.initialize_yolo_model.return_value = MagicMock()
    monkeypatch.setitem(sys.modules, "utils", fake_utils)

    sys.modules.pop("segmentation", None)
    return importlib.import_module("segmentation")


def test_native_yolo_imgsz_uses_uploaded_image_dimensions(monkeypatch):
    segmentation = _load_segmentation(monkeypatch)

    img = np.zeros((721, 1283, 3), dtype=np.uint8)
    assert segmentation._native_yolo_imgsz(img) == (721, 1283)


def test_decode_image_for_cv_applies_exif_orientation(monkeypatch):
    segmentation = _load_segmentation(monkeypatch)

    source = Image.new("RGB", (20, 10), "white")
    exif = source.getexif()
    exif[274] = 6  # Rotate 90 degrees clockwise for display.
    buf = BytesIO()
    source.save(buf, format="JPEG", exif=exif.tobytes())

    decoded = segmentation._decode_image_for_cv(buf.getvalue())

    assert decoded.shape[:2] == (20, 10)


def test_select_closest_box_uses_largest_area(monkeypatch):
    segmentation = _load_segmentation(monkeypatch, use_real_torch=True)

    boxes = segmentation.torch.tensor(
        [
            [0.0, 0.0, 10.0, 10.0],
            [0.0, 0.0, 30.0, 20.0],
            [0.0, 0.0, 15.0, 15.0],
        ]
    )

    selected = segmentation._select_closest_box(boxes)

    assert selected.shape == (1, 4)
    assert selected.tolist() == [[0.0, 0.0, 30.0, 20.0]]


def test_select_closest_box_keeps_empty_tensor(monkeypatch):
    segmentation = _load_segmentation(monkeypatch, use_real_torch=True)

    boxes = segmentation.torch.empty((0, 4))

    selected = segmentation._select_closest_box(boxes)

    assert selected.shape == (0, 4)
