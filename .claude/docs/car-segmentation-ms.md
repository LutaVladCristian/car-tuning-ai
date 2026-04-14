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
├── server.py          # FastAPI endpoints (car-segmentation, car-part-segmentation, edit-photo)
├── segmentation.py    # Core CV logic: YOLO detection → SAM mask generation
├── utils.py           # Model initialization, mask utilities
└── environment-local.yml
```

`server.py` imports the current `segmentation.py` module directly.

## Model Weights (gitignored)

Place in `car-segmentation-ms/model/`:
- `sam_vit_b_01ec64.pth` — SAM ViT-Base
- `yolov11seg.pt` — YOLOv11 segmentation (car part detection)
- `yolov10n.pt` — YOLOv10n (full car detection)

## API Endpoints

| Method | Path | Input | Output |
|---|---|---|---|
| POST | `/car-segmentation` | `file` (image), `inverse` (bool) | PNG — car isolated or background isolated |
| POST | `/car-part-segmentation` | `file`, `carPartId` (int), `inverse` (bool) | PNG — specific car part masked |
| POST | `/edit-photo` | `file`, `prompt` (str), `edit_car` (bool), `size` (str) | PNG — AI-edited result |

`/edit-photo` writes intermediate files to `output/image.png` and `output/mask.png`, then calls `gpt-image-1` via the OpenAI API.

## ML Pipeline

```
Input image
    │
    ▼ YOLOv10n (full car detection)
Bounding box
    │
    ▼ SAM ViT-Base (mask generation from bbox prompt)
Binary mask
    │
    ├─ (car-segmentation) → apply mask to isolate car/background
    └─ (car-part-segmentation) → YOLOv11seg detects part within car bbox → SAM mask → apply
```

**`apply_binary_mask_for_inpainting()` steps** (`utils.py`):
1. Resize image to `size` (e.g., `1024x1536`) if provided
2. Save `output/image.png`
3. Threshold mask → binary
4. Invert mask if `inverse=True`
5. GaussianBlur 5×5 for soft edges
6. Convert to RGBA; alpha channel = mask
7. Save `output/mask.png`
8. Return numpy RGBA array

**Failure modes:**
- No car detected by YOLOv10n → HTTP 400: `"No cars detected in the image"`
- CUDA unavailable → silently falls back to CPU (inference is significantly slower)
- OpenAI API error → propagates as HTTP 500