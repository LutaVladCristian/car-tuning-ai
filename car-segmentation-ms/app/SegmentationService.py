import numpy as np
import cv2
import torch
import os
from dotenv import load_dotenv
import base64

from app.Utils import initialize_sam_model, initialize_yolo_model, apply_binary_mask_for_inpainting


# Define a working directory
working_dir = "C:/Users/vlad_cristian.luta/PycharmProjects/car-tuning-ai/car-segmentation-ms/app"

# Define device
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Constants for initialization
SAM_CHECKPOINT_PATH = working_dir + "/model/sam_vit_b_01ec64.pth"
SAM_MODEL_TYPE = "vit_b"
YOLO_SEG_MODEL_PATH = working_dir + '/model/yolov11seg.pt'
YOLO_DETECTION_MODEL_PATH = working_dir + '/model/yolov10n.pt'

# Initialize models
sam_predictor = initialize_sam_model(SAM_CHECKPOINT_PATH, SAM_MODEL_TYPE, DEVICE)
yolo_segmentation_model = initialize_yolo_model(YOLO_SEG_MODEL_PATH, DEVICE)
yolo_detection_model = initialize_yolo_model(YOLO_DETECTION_MODEL_PATH, DEVICE)


def segment_car(content, inverse=True, size="1024x1536"):
    """Segment cars from an input image."""
    # Decode binary content into a NumPy array

    file_bytes = np.frombuffer(content, np.uint8)

    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    if img is None:
        raise TypeError("Failed to decode image. Ensure the input is a valid image file.")

    # Perform prediction using YOLO
    results_yolo = yolo_detection_model.predict(img, classes=[2], conf=0.75)
    boxes_yolo = results_yolo[0].boxes.xyxy if len(results_yolo) > 0 else []

    if len(boxes_yolo) == 0:
        return {"message": "No cars detected in image."}

    sam_predictor.set_image(img)

    transformed_boxes = sam_predictor.transform.apply_boxes_torch(
        boxes_yolo.clone().detach().to(sam_predictor.device),
        img.shape[:2]
    )

    car_mask = sam_predictor.predict_torch(
        point_coords=None,
        point_labels=None,
        boxes=transformed_boxes,
        multimask_output=False,
    )

    # Convert mask to numpy
    mask_np = car_mask[0][0].cpu().numpy()  # shape: (1, H, W) -> need squeeze
    mask_np = np.squeeze(mask_np)  # shape: (H, W)
    mask_np = (mask_np * 255).astype(np.uint8)

    # Save the mask as JPEG
    output_dir = os.path.join(working_dir + "\output")

    return apply_binary_mask_for_inpainting(img, mask_np, output_dir, inverse, size)


def segment_car_part(content, target_class_id=22, inverse=False, size="1024x1536"):
    """Run YOLOv11 segmentation and save mask for a specific class (e.g., wheels, lights, etc.)."""

    # Decode the image from binary content
    file_bytes = np.frombuffer(content, np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    if img is None:
        raise TypeError("Invalid image input. Ensure it is a valid image file.")

    # Run YOLOv11 with segmentation task
    results = yolo_segmentation_model.predict(img, conf=0.5, task='segment')

    # Check if masks are present
    if not hasattr(results[0], "masks") or results[0].masks is None:
        return {"message": "No segmentation masks found."}

    masks = results[0].masks.data.cpu().numpy()      # shape: (N, H, W)
    classes = results[0].boxes.cls.cpu().numpy()     # shape: (N,)

    # Initialize an empty mask
    class_mask = np.zeros_like(masks[0], dtype=np.uint8)

    # Combine masks for the target class(es)
    for i, class_id in enumerate(classes):
        if int(class_id) == target_class_id or (isinstance(target_class_id, list) and int(class_id) in target_class_id):
            class_mask = np.logical_or(class_mask, masks[i])

    # Convert boolean mask to uint8
    mask_np = (class_mask * 255).astype(np.uint8)

    # Save the mask
    output_dir = os.path.join(working_dir, "output")

    return apply_binary_mask_for_inpainting(img, mask_np, output_dir, inverse, size)


# For testing
input_image = working_dir + "/input/side.jpeg"

if __name__ == "__main__":
    with open(input_image, "rb") as f:
        input_image = f.read()

    segment_car(input_image)
    #segment_car_part(input_image, target_class_id=22)