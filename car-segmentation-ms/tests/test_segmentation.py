import importlib
import sys
from unittest.mock import MagicMock

import numpy as np


def test_native_yolo_imgsz_uses_uploaded_image_dimensions(monkeypatch):
    fake_torch = MagicMock()
    fake_torch.device.return_value = "cpu"
    monkeypatch.setitem(sys.modules, "torch", fake_torch)

    fake_utils = MagicMock()
    fake_utils.initialize_sam_model.return_value = MagicMock()
    fake_utils.initialize_yolo_model.return_value = MagicMock()
    monkeypatch.setitem(sys.modules, "utils", fake_utils)

    sys.modules.pop("segmentation", None)
    segmentation = importlib.import_module("segmentation")

    img = np.zeros((721, 1283, 3), dtype=np.uint8)
    assert segmentation._native_yolo_imgsz(img) == (721, 1283)
