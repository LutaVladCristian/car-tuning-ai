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


def test_pick_primary_mask_returns_mask_with_most_pixels(monkeypatch):
    segmentation = _load_segmentation(monkeypatch, use_real_torch=True)

    # Three masks: 100 px, 900 px (largest), 400 px
    masks = segmentation.torch.zeros(3, 1, 30, 30, dtype=segmentation.torch.bool)
    masks[0, 0, :10, :10] = True
    masks[1, 0, :30, :30] = True  # largest — should be selected
    masks[2, 0, :20, :20] = True

    result = segmentation._pick_primary_mask(masks)

    assert result.shape == (30, 30)
    assert int(result.sum()) == 900
