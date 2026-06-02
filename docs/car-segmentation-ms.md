# car-segmentation-ms

Internal FastAPI ML inference service: YOLO car detection, SAM masking, and OpenAI image editing.

**Conda env:** `sam-microservice`
**Port:** 8000 locally; Cloud Run uses the injected `PORT` value.
**Auth:** no app-level auth locally. Cloud Run IAM protects production.

## Model Weights

Place these gitignored files in `car-segmentation-ms/model/` before local development or Docker builds:

- `sam_vit_h_4b8939.pth` - SAM ViT-H
- `yolov10n.pt` - YOLOv10n COCO detector for class `2 = car`

The Dockerfile copies the weights into `/app/model/`. There is no runtime model download.

## API Endpoints

| Method | Path | Input | Output |
|---|---|---|---|
| GET | `/health` | none | `{"status":"ok"}` after model initialization; HTTP 503 while loading |
| POST | `/segment-photo` | `file`, `edit_car`, `size` | Prepared PNG, raw binary car mask, and effective OpenAI RGBA mask as base64 |
| POST | `/generate-photo` | prepared `file`, effective `mask`, `prompt`, `size` | Generated result PNG as base64 |

## Pipeline

`/segment-photo` decodes the upload with EXIF orientation, validates dimensions, detects the closest car with YOLOv10n, refines that box with SAM ViT-H, and writes:

- `image.png`: prepared input image.
- `raw-mask.png`: binary SAM car mask with white car pixels and black background.
- `mask.png`: OpenAI-compatible RGBA mask where alpha `0` is editable.

For background edits, the protected car mask is expanded slightly to preserve wheels, mirrors, trim, and edges. `/generate-photo` calls `gpt-image-1` only after the user approves the masks in the frontend.

## Startup

Models load in a background thread so uvicorn binds the port immediately. `/health`, `/segment-photo`, and `/generate-photo` return HTTP 503 until initialization finishes. Production Cloud Run deployment uses `/health` as an HTTP startup probe with a 120-second retry window so traffic is not routed to an unready instance.
