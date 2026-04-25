# car-segmentation-ms

Internal FastAPI ML inference service — YOLO detection, SAM masking, and OpenAI image editing.

**Conda env:** `sam-microservice` (Python 3.10, PyTorch 2.2.0 + heavy ML deps — note: differs from `car-backend-ms` which uses Python 3.12)
**Port:** 8000 (not exposed publicly — backend proxies to it)
**No auth** — accessible only from within the same network/host as `car-backend-ms`.

## Commands

See [README.md](../../README.md) for commands.

## Structure

```
car-segmentation-ms/
├── server.py          # FastAPI endpoint (/edit-photo)
├── segmentation.py    # Core CV logic: YOLO detection → SAM mask generation
├── utils.py           # Model initialization, mask utilities
└── environment-local.yml
```

`server.py` imports the current `segmentation.py` module directly.

## Model Weights (gitignored)

Place in `car-segmentation-ms/model/`:
- `sam_vit_h_4b8939.pth` — SAM ViT-H
- `yolov11n.pt` — YOLOv11n (car detection)

## API Endpoints

| Method | Path | Input | Output |
|---|---|---|---|
| GET | `/health` | — | `{"status":"ok"}` once models are ready; HTTP 503 while loading |
| POST | `/edit-photo` | `file` (image), `prompt` (str), `edit_car` (bool), `size` (str) | PNG — AI-edited result; HTTP 503 if models are still loading |

`/edit-photo` writes intermediate files to a per-request temp dir `output/request-<uuid>/` (cleaned up in a `finally` block after the OpenAI call), then calls `gpt-image-1` via the OpenAI API.

## ML Pipeline

```
Input image
    │
    ▼ YOLOv11n (full car detection)
Bounding box
    │
    ▼ SAM ViT-H (mask generation from bbox prompt)
Binary mask
    │
    └─ (edit-photo) → apply mask for inpainting → OpenAI gpt-image-1 → PNG result
```

**`apply_binary_mask_for_inpainting()` steps** (`utils.py`):
1. Resize image to `size` (e.g., `1024x1536`) if provided
2. Save `<tmp_dir>/image.png`
3. Threshold mask → binary
4. Invert mask if `inverse=True`
5. GaussianBlur 5×5 for soft edges
6. Convert to RGBA; alpha channel = mask
7. Save `<tmp_dir>/mask.png`
8. Return numpy RGBA array

## Startup Behaviour

Models are loaded in a background thread via `asyncio.to_thread` so uvicorn binds the port immediately. Cloud Run's TCP startup probe passes as soon as the port opens; `download_models.py` and model weight loading into GPU memory then complete in the background. `GET /health` and `POST /edit-photo` both return HTTP 503 until `_models_ready` is set.

`download_models.py` is no longer called from the Dockerfile `CMD` — it is imported and called inside `_load_models()` in `server.py`.

**Failure modes:**
- Models not yet ready → HTTP 503: `"Models still loading, try again shortly"`
- No car detected by YOLOv11n → HTTP 400: `"No cars detected in the image"`
- CUDA unavailable → silently falls back to CPU (inference is significantly slower)
- OpenAI API error → propagates as HTTP 500