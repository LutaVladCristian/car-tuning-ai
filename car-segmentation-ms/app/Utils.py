from segment_anything import sam_model_registry, SamPredictor
from ultralytics import YOLO
import cv2
import numpy as np
import os
from PIL import Image

def initialize_sam_model(checkpoint_path, model_type, device):
    """Initialize the SAM model."""
    sam_model = sam_model_registry[model_type](checkpoint=checkpoint_path).to(device)
    return SamPredictor(sam_model)

def initialize_yolo_model(model_path, device):
    """Initialize a YOLO model."""
    model = YOLO(model_path)
    model.to(device)
    return model

def apply_binary_mask_for_inpainting(image, mask, output_dir, inverse=False, size=None):
    """
    Processes an image and its mask to produce a valid inpainting mask with an alpha channel:
    - Car area is black (0)
    - Background is white (255)
    - An alpha channel is derived from binary mask
    Saves each step into the specified output directory.
    """

    os.makedirs(output_dir, exist_ok=True)

    if size:
        photo_size = tuple(map(int, size.split("x")))
        print(photo_size)
        image = cv2.resize(image, photo_size)

    # Save the original image
    cv2.imwrite(os.path.join(output_dir, "image.png"), image)

    # Ensure the mask is grayscale
    if mask.ndim == 3:
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)

    # Resize mask to match the image size
    mask = cv2.resize(mask, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_NEAREST)

    # Threshold mask to binary
    _, binary_mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)

    # Invert mask if needed
    inpaint_mask = cv2.bitwise_not(binary_mask) if inverse else binary_mask
    #cv2.imwrite(os.path.join(output_dir, "2_inpainting_mask.png"), inpaint_mask)

    # Optional blurred version
    blurred_mask = cv2.GaussianBlur(inpaint_mask, (5, 5), 10)
    #cv2.imwrite(os.path.join(output_dir, "3_blurred_mask_visual.png"), blurred_mask)

    # Create an alpha-enabled mask image using PIL
    pil_mask = Image.fromarray(blurred_mask).convert("L")
    pil_rgba = pil_mask.convert("RGBA")
    pil_rgba.putalpha(pil_mask)  # Add grayscale as alpha

    # Save RGBA mask
    mask_with_alpha_path = os.path.join(output_dir, "mask.png")
    pil_rgba.save(mask_with_alpha_path)

    return np.array(pil_rgba)