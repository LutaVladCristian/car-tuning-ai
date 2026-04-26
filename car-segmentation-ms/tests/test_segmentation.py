import importlib
import sys
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pytest
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


def test_yolo_imgsz_caps_at_640(monkeypatch):
    segmentation = _load_segmentation(monkeypatch)

    small = np.zeros((480, 640, 3), dtype=np.uint8)
    assert segmentation._yolo_imgsz(small) == 640

    large = np.zeros((2160, 3840, 3), dtype=np.uint8)
    assert segmentation._yolo_imgsz(large) == 640


def test_decode_image_for_cv_applies_exif_orientation(monkeypatch):
    segmentation = _load_segmentation(monkeypatch)

    source = Image.new("RGB", (20, 10), "white")
    exif = source.getexif()
    exif[274] = 6  # Rotate 90 degrees clockwise for display.
    buf = BytesIO()
    source.save(buf, format="JPEG", exif=exif.tobytes())

    decoded = segmentation._decode_image_for_cv(buf.getvalue())

    assert decoded.shape[:2] == (20, 10)


def test_select_closest_car_box_prefers_larger_lower_detection(monkeypatch):
    segmentation = _load_segmentation(monkeypatch, use_real_torch=True)

    boxes = segmentation.torch.tensor(
        [
            [20.0, 10.0, 70.0, 40.0],
            [10.0, 40.0, 90.0, 95.0],
            [35.0, 50.0, 60.0, 85.0],
        ]
    )

    selected = segmentation._select_closest_car_box(boxes, (100, 100))

    assert selected.shape == (1, 4)
    assert selected.tolist() == [[10.0, 40.0, 90.0, 95.0]]


def test_detect_car_boxes_raises_when_no_cars_detected(monkeypatch):
    segmentation = _load_segmentation(monkeypatch, use_real_torch=True)
    segmentation.yolo_detection_model.predict.return_value = [
        SimpleNamespace(boxes=SimpleNamespace(xyxy=segmentation.torch.empty((0, 4))))
    ]

    with pytest.raises(ValueError, match="No cars detected in image."):
        segmentation._detect_car_boxes(np.zeros((100, 100, 3), dtype=np.uint8))


def test_segment_car_calls_sam_with_one_selected_box(monkeypatch, tmp_path):
    segmentation = _load_segmentation(monkeypatch, use_real_torch=True)

    source = Image.new("RGB", (100, 100), "white")
    buf = BytesIO()
    source.save(buf, format="PNG")

    boxes = segmentation.torch.tensor(
        [
            [20.0, 10.0, 70.0, 40.0],
            [10.0, 40.0, 90.0, 95.0],
        ]
    )
    segmentation.yolo_detection_model.predict.return_value = [
        SimpleNamespace(boxes=SimpleNamespace(xyxy=boxes))
    ]
    segmentation.sam_predictor.device = "cpu"
    segmentation.sam_predictor.transform.apply_boxes_torch.side_effect = lambda value, _: value
    masks = segmentation.torch.zeros((1, 1, 100, 100), dtype=segmentation.torch.bool)
    masks[0, 0, 40:95, 10:90] = True
    segmentation.sam_predictor.predict_torch.return_value = (masks, None, None)

    segmentation.segment_car(buf.getvalue(), edit_car=True, output_dir=str(tmp_path))

    boxes_arg = segmentation.sam_predictor.predict_torch.call_args.kwargs["boxes"]
    assert boxes_arg.shape == (1, 4)
    assert boxes_arg.tolist() == [[10.0, 40.0, 90.0, 95.0]]
