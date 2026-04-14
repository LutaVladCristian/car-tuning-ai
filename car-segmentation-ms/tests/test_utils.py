import os
import tempfile

import numpy as np
import pytest
from utils import apply_binary_mask_for_inpainting

# A small solid-white 10x10 BGR image
WHITE_IMAGE = np.full((10, 10, 3), 255, dtype=np.uint8)
# A solid-white mask (all foreground)
WHITE_MASK = np.full((10, 10), 255, dtype=np.uint8)
# A solid-black mask (no foreground)
BLACK_MASK = np.zeros((10, 10), dtype=np.uint8)


@pytest.fixture()
def out_dir(tmp_path):
    return str(tmp_path)


class TestApplyBinaryMaskForInpainting:
    def test_returns_rgba_array(self, out_dir):
        result = apply_binary_mask_for_inpainting(WHITE_IMAGE, WHITE_MASK, out_dir)
        assert isinstance(result, np.ndarray)
        assert result.ndim == 3
        assert result.shape[2] == 4  # RGBA

    def test_output_shape_matches_input(self, out_dir):
        result = apply_binary_mask_for_inpainting(WHITE_IMAGE, WHITE_MASK, out_dir)
        assert result.shape[:2] == WHITE_IMAGE.shape[:2]

    def test_saves_image_png(self, out_dir):
        apply_binary_mask_for_inpainting(WHITE_IMAGE, WHITE_MASK, out_dir)
        assert os.path.exists(os.path.join(out_dir, "image.png"))

    def test_saves_mask_png(self, out_dir):
        apply_binary_mask_for_inpainting(WHITE_IMAGE, WHITE_MASK, out_dir)
        assert os.path.exists(os.path.join(out_dir, "mask.png"))

    def test_creates_output_dir_if_missing(self, tmp_path):
        new_dir = str(tmp_path / "nested" / "output")
        apply_binary_mask_for_inpainting(WHITE_IMAGE, WHITE_MASK, new_dir)
        assert os.path.isdir(new_dir)

    def test_inverse_produces_different_alpha(self, out_dir):
        with tempfile.TemporaryDirectory() as out_dir2:
            normal = apply_binary_mask_for_inpainting(WHITE_IMAGE, WHITE_MASK, out_dir)
            inverted = apply_binary_mask_for_inpainting(WHITE_IMAGE, WHITE_MASK, out_dir2, inverse=True)
        # Alpha channels should differ when mask is non-trivial
        assert not np.array_equal(normal[:, :, 3], inverted[:, :, 3])

    def test_3d_mask_is_accepted(self, out_dir):
        """A 3-channel mask should be converted to grayscale without error."""
        mask_3d = np.full((10, 10, 3), 200, dtype=np.uint8)
        result = apply_binary_mask_for_inpainting(WHITE_IMAGE, mask_3d, out_dir)
        assert result.shape[2] == 4

    def test_size_param_resizes_output(self, out_dir):
        result = apply_binary_mask_for_inpainting(WHITE_IMAGE, WHITE_MASK, out_dir, size="20x20")
        assert result.shape[:2] == (20, 20)
