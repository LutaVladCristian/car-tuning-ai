# car-segmentation-ms

Internal FastAPI ML inference service — YOLO detection, SAM masking, and OpenAI image editing.

**Conda env:** `sam-microservice` (Python 3.12, PyTorch + heavy ML deps)
**Port:** 8000 (not exposed publicly — backend proxies to it)
**No auth** — accessible only from within the same network/host as `car-backend-ms`.

## Commands

```bash
conda activate sam-microservice
cd car-segmentation-ms

uvicorn server:app --reload --port 8000
```

There are currently no automated tests. The ML pipeline requires GPU and model weights to run.

## Structure

```
car-segmentation-ms/
├── server.py          # FastAPI endpoints (car-segmentation, car-part-segmentation, edit-photo)
├── segmentation.py    # Core CV logic: YOLO detection → SAM mask generation
├── utils.py           # Model initialization, mask utilities
└── environment-local.yml
```

> **Note:** `server.py` currently imports `from SegmentationService import ...` — this is a stale reference from a rename. The actual module is `segmentation.py`. This import will fail until fixed.

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

`/edit-photo` writes intermediate files to `output/image.png` and `output/mask.png` under `WORKING_DIR`, then calls `gpt-image-1` via the OpenAI API.

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

## Docker

The Docker image is large (~5–10 GB) due to PyTorch + CUDA. GPU access is required at runtime.

```bash
docker build -t car-segmentation-ms ./car-segmentation-ms
docker run --gpus all -p 8000:8000 \
  -e OPENAI_API_KEY=sk-... \
  -e WORKING_DIR=/app \
  car-segmentation-ms
```

Use `nvidia/cuda` base image in the Dockerfile for GPU support. Without GPU, inference falls back to CPU (very slow).
