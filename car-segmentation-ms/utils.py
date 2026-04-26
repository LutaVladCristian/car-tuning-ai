import os

import cv2
import numpy as np
from PIL import Image
from segment_anything import SamPredictor, sam_model_registry
from ultralytics import YOLO

_BACKGROUND_PROTECT_MARGIN_RATIO = 0.008
_BACKGROUND_PROTECT_MARGIN_MIN_PX = 6
_BACKGROUND_PROTECT_MARGIN_MAX_PX = 24


def initialize_sam_model(checkpoint_path, model_type, device):
    """Initialize the SAM model."""
    sam_model = sam_model_registry[model_type](checkpoint=checkpoint_path).to(device)
    return SamPredictor(sam_model)


def initialize_yolo_model(model_path, device):
    """Initialize a YOLO model."""
    model = YOLO(model_path)
    model.to(device)
    return model


def _expand_mask_for_background_edit(binary_mask):
    """Protect a small margin around the car when only the background is editable."""
    height, width = binary_mask.shape[:2]
    radius = int(round(min(height, width) * _BACKGROUND_PROTECT_MARGIN_RATIO))
    radius = max(_BACKGROUND_PROTECT_MARGIN_MIN_PX, min(_BACKGROUND_PROTECT_MARGIN_MAX_PX, radius))
    kernel_size = (radius * 2) + 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    return cv2.dilate(binary_mask, kernel, iterations=1)


def apply_binary_mask_for_inpainting(image, mask, output_dir, edit_car=False, size=None):
    """
    Save image.png and an OpenAI-compatible mask.png.

    The input mask uses white pixels for the SAM car foreground. OpenAI image
    edits use alpha=0 for editable pixels and alpha=255 for protected pixels.
    Background edits expand the protected car mask slightly so the image model
    does not repaint car edges, wheels, mirrors, or trim into a different scale.
    """

    os.makedirs(output_dir, exist_ok=True)

    if size and size != "auto":
        parts = size.split("x")
        if len(parts) != 2:
            raise ValueError(f"Invalid size format {size!r}. Expected WxH (e.g. '1024x1536').")
        w, h = int(parts[0]), int(parts[1])
        max_dim = 4096
        if not (1 <= w <= max_dim and 1 <= h <= max_dim):
            raise ValueError(f"Dimensions {w}x{h} out of range. Each must be 1-{max_dim}.")
        image = cv2.resize(image, (w, h))

    cv2.imwrite(os.path.join(output_dir, "image.png"), image)

    if mask.ndim == 3:
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)

    mask = cv2.resize(mask, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_NEAREST)
    _, binary_mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)

    if not edit_car:
        binary_mask = _expand_mask_for_background_edit(binary_mask)

    car_pixels = binary_mask == 255
    editable_pixels = car_pixels if edit_car else ~car_pixels
    alpha = np.where(editable_pixels, 0, 255).astype(np.uint8)

    pil_alpha = Image.fromarray(alpha, mode="L")
    pil_rgba = Image.new("RGBA", pil_alpha.size, (0, 0, 0, 255))
    pil_rgba.putalpha(pil_alpha)

    mask_with_alpha_path = os.path.join(output_dir, "mask.png")
    pil_rgba.save(mask_with_alpha_path)

    return np.array(pil_rgba)
