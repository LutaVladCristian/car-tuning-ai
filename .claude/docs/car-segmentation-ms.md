# car-segmentation-ms

Internal FastAPI ML inference service: YOLO car detection, SAM masking, and OpenAI image editing.

**Conda env:** `sam-microservice` (Python 3.10, PyTorch 2.8.0 + heavy ML deps; differs from `car-backend-ms`, which uses Python 3.12)
**Port:** 8000 locally; Cloud Run uses the injected `PORT` value.
**Auth:** no app-level auth locally. In production, Cloud Run IAM protects the service and the backend calls it with a GCP identity token.

## Commands

See [README.md](../../README.md) for setup, model weights, local run commands, and tests.

## Structure

```
car-segmentation-ms/
|-- server.py          # FastAPI app, /health, /edit-photo, OpenAI call
|-- segmentation.py    # Core CV pipeline: YOLOv10n closest-car box -> SAM mask
|-- utils.py           # Model initialization and OpenAI-compatible mask export
|-- download_models.py # GCS model download used during service startup
`-- environment-local.yml
```

`server.py` imports the current `segmentation.py` module directly after `download_models()` runs during background model loading.

## Model Weights

Place in `car-segmentation-ms/model/` for local development, or upload these exact filenames to the GCS bucket named by `MODEL_BUCKET` for deployment:

- `sam_vit_h_4b8939.pth` - SAM ViT-H (~2.5 GB)
- `yolov10n.pt` - YOLOv10n COCO detector used for class `2 = car`

Note: the local `yolo11n.pt` file in older setups is a car-parts model, not the COCO car detector used by this pipeline.

## API Endpoints

| Method | Path | Input | Output |
|---|---|---|---|
| GET | `/health` | none | `{"status":"ok"}` once models are ready; HTTP 503 while loading |
| POST | `/edit-photo` | `file` image, `prompt` string, `edit_car` bool, `size` string | PNG AI-edited result; HTTP 503 if models are still loading |

`/edit-photo` writes `image.png` and `mask.png` to a per-request temp dir under `output/request-<uuid>/`, calls `gpt-image-1` through the OpenAI Images API, then removes the temp dir in a `finally` block.

## ML Pipeline

```
Input image bytes
    |
    v
Decode with EXIF orientation -> OpenCV BGR
    |
    v
Validate dimensions (max 4096 px per side and 4096*4096 total pixels)
    |
    v
YOLOv10n COCO detection (class 2 = car, conf 0.25, imgsz <= 640)
    |
    v
Select one closest-car box by area plus lower frame position
    |
    v
SAM ViT-H mask for that one selected box (multimask_output=False)
    |
    v
apply_binary_mask_for_inpainting()
    |
    v
OpenAI gpt-image-1 edit -> PNG result
```

**Car selection:** `_select_closest_car_box()` approximates the closest visible car from a 2D photo by combining bounding-box area with the box's lower position in the frame. SAM runs only on the selected box, so exactly one car mask is sent to OpenAI.

**YOLO inference size:** `_YOLO_IMGSZ = 640`; uploads smaller than 640 use their larger side, and larger uploads are capped at 640 for YOLO inference. SAM still receives the full image for accurate mask boundaries.

**Mask semantics:** the SAM car foreground is white in the binary mask. `apply_binary_mask_for_inpainting()` converts it into an OpenAI-compatible RGBA mask:

1. Resize `image` to explicit `size` when provided.
2. Save `<tmp_dir>/image.png`.
3. Convert/resize/threshold the SAM mask so it matches `image.png`.
4. If `edit_car=True`, make car pixels transparent and background opaque.
5. If `edit_car=False`, make background pixels transparent and car pixels opaque.
6. Save `<tmp_dir>/mask.png`; alpha `0` means OpenAI may edit that pixel, alpha `255` means protected.

For `size="auto"`, `server.py` sends `size="auto"` to OpenAI and resizes the returned image back to the original source dimensions if needed.

## Startup Behaviour

Models are loaded in a background thread via `asyncio.to_thread` so uvicorn binds the port immediately. Cloud Run's TCP startup probe passes as soon as the port opens; `download_models.py` and model weight loading into GPU memory then complete in the background. `GET /health` and `POST /edit-photo` both return HTTP 503 until `_models_ready` is set.

`download_models.py` downloads missing model files from the GCS bucket named by `MODEL_BUCKET`. If local model files are missing and `MODEL_BUCKET` is unset, startup raises a clear error.

**Failure modes:**

- Models not yet ready -> HTTP 503: `"Models still loading, try again shortly"`
- Invalid/oversized image -> HTTP 400 from segmentation helpers or 413/415 from backend validation
- No car detected by YOLOv10n -> HTTP 400: `"No cars detected in image."`
- CUDA unavailable -> falls back to CPU, but inference is significantly slower
- OpenAI API error -> propagates as HTTP 500 from the segmentation service
