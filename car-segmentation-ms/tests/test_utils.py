import cv2
import numpy as np
from PIL import Image

from utils import apply_binary_mask_for_inpainting, initialize_sam_model, initialize_yolo_model


def test_initialize_sam_model_wraps_model_in_predictor():
    predictor = initialize_sam_model("sam.pth", "vit_b", "cpu")

    assert predictor.model.checkpoint == "sam.pth"
    assert predictor.model.device == "cpu"


def test_initialize_yolo_model_moves_model_to_device():
    model = initialize_yolo_model("yolo.pt", "cuda")

    assert model.model_path == "yolo.pt"
    assert model.device == "cuda"


def test_apply_binary_mask_for_inpainting_writes_image_and_rgba_mask(tmp_path):
    image = np.zeros((4, 4, 3), dtype=np.uint8)
    image[:, :] = [10, 20, 30]
    mask = np.zeros((4, 4), dtype=np.uint8)
    mask[1:3, 1:3] = 255

    result = apply_binary_mask_for_inpainting(image, mask, str(tmp_path), inverse=False)

    assert result.shape == (4, 4, 4)
    assert (tmp_path / "image.png").exists()
    assert (tmp_path / "mask.png").exists()

    saved_mask = Image.open(tmp_path / "mask.png")
    assert saved_mask.mode == "RGBA"

    alpha = np.array(saved_mask.getchannel("A"))
    assert alpha[2, 2] > alpha[0, 0]


def test_apply_binary_mask_for_inpainting_inverts_mask(tmp_path):
    image = np.zeros((4, 4, 3), dtype=np.uint8)
    mask = np.zeros((4, 4), dtype=np.uint8)
    mask[1:3, 1:3] = 255

    apply_binary_mask_for_inpainting(image, mask, str(tmp_path), inverse=True)

    saved_mask = Image.open(tmp_path / "mask.png")
    alpha = np.array(saved_mask.getchannel("A"))
    assert alpha[0, 0] > alpha[2, 2]


def test_apply_binary_mask_for_inpainting_resizes_outputs(tmp_path):
    image = np.zeros((4, 4, 3), dtype=np.uint8)
    mask = np.ones((4, 4), dtype=np.uint8) * 255

    result = apply_binary_mask_for_inpainting(image, mask, str(tmp_path), size="8x6")

    saved_image = cv2.imread(str(tmp_path / "image.png"))
    assert result.shape == (6, 8, 4)
    assert saved_image.shape[:2] == (6, 8)
