# CLAUDE.md — Car Tuning AI

## Project Overview

An AI-powered car image manipulation REST API. The system allows users to upload car photos, isolate the car or specific parts (wheels, lights, etc.), and apply AI-driven edits (background replacement, color changes, etc.) via HTTP endpoints.

**Current stage:** MVP — single microservice, no frontend yet.

---

## Architecture

Single microservice built in Python. No inter-service communication.

```
car-tuning-ai/
├── CLAUDE.md
├── README.md
├── environment.yml                 # Conda environment (Python 3.9)
├── .env                            # OPENAI_API_KEY, WORKING_DIR
├── user_flow_decision_tree.txt    # Product feature planning document
└── car-segmentation-ms/           # The only microservice
    ├── server.py                  # FastAPI app + endpoint definitions
    ├── SegmentationService.py     # Core CV logic (YOLO + SAM)
    ├── Utils.py                   # Model init + mask utilities
    ├── model/                     # Downloaded model weights (gitignored)
    ├── input/                     # Test images (gitignored)
    └── output/                    # Generated outputs (gitignored)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.9 |
| Web framework | FastAPI + Uvicorn |
| Car detection | YOLOv10n (`yolov10n.pt`) |
| Part segmentation | YOLOv11 seg (`yolov11seg.pt`) |
| Mask generation | SAM ViT-Base (`sam_vit_b_01ec64.pth`) |
| Image I/O | OpenCV, Pillow, NumPy |
| AI editing | OpenAI API (`gpt-image-1`) |
| Environment | Conda (`sam-microservice`) |
| GPU | PyTorch CUDA (auto-detects GPU/CPU) |

---

## REST API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/car-segmentation` | Isolate full car from background |
| POST | `/car-part-segmentation` | Isolate a specific car part by class ID |
| POST | `/edit-photo` | Replace/edit background using OpenAI image API |
| GET | `/docs` | Swagger UI |

All image endpoints accept `multipart/form-data` and return PNG binary streams (except `/edit-photo` which returns JSON with base64).

---

## Image Processing Pipeline

1. Client uploads binary image
2. YOLOv10 detects car bounding box (class 2, confidence ≥ 0.75)
3. SAM uses bounding box to generate precise binary mask
4. Mask is normalized (0–255 uint8), optionally inverted
5. Gaussian blur applied (5×5 kernel, σ=10)
6. Alpha channel added → output as RGBA PNG

For part segmentation, YOLOv11 seg replaces step 2–3, targeting a `target_class_id`.

---

## Environment Setup

```bash
conda env create -f environment.yml
conda activate sam-microservice
cd car-segmentation-ms
uvicorn server:app --reload
```

Server runs at `http://localhost:8000`.

Models must be manually downloaded and placed in `car-segmentation-ms/model/`:
- `sam_vit_b_01ec64.pth`
- `yolov10n.pt`
- `yolov11seg.pt`

`.env` must define:
```
OPENAI_API_KEY=sk-proj-...
WORKING_DIR=<absolute path to car-segmentation-ms>
```

---

## Known Issues / Limitations

- **Hardcoded Windows paths** in `SegmentationService.py` (`working_dir = "C:/Users/..."`) — needs to be replaced with env var or relative path resolution.
- No authentication on any endpoint.
- No database or state — fully stateless API.
- `/edit-photo` depends on OpenAI API key and credits.
- Models are large binary files — gitignored, must be obtained separately.

---

## Planned Features (from `user_flow_decision_tree.txt`)

- MVP: Change car color (mask creation + color-modified generation)
- Spoilers, rims, body kits, lighting modifications
- Background / environment changes (weather, location, lighting style)
- User-drawn masks for custom region selection

---

## Git Branches

- `main` — stable base
- `car-segmentation-ms` — active development branch for the segmentation microservice

---

## Development Notes

- Future microservices should follow the same FastAPI pattern and be added as sibling directories to `car-segmentation-ms/`.
- Keep model weights out of git — use `model/` directory with `.gitignore`.
- The `environment.yml` is the source of truth for dependencies — do not use plain `pip install` outside of it.
