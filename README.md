# Car Tuning AI

An AI-powered car image manipulation platform. Users upload car photos, isolate the car or specific parts, and apply AI-driven edits.

## Prerequisites

- [Conda](https://docs.conda.io/en/latest/miniconda.html) (Miniconda or Anaconda)
- [Node.js](https://nodejs.org/) v22+
- GPU with CUDA support (required for ML inference in `car-segmentation-ms`; CPU fallback is very slow)

## Environment Variables

Copy the template and fill in the required values:

```bash
cp .env.example .env
```

Edit `.env` at the repo root. See `.env.example` for all required variables and their descriptions.

## Model Weights

Download and place the following files under `car-segmentation-ms/model/`:

- `sam_vit_h_4b8939.pth` — SAM ViT-H (~2.5 GB)
- `yolo11n.pt` — YOLO11n car detection (~6 MB; auto-downloaded by Ultralytics on first run)

## One-Time Setup

### Create Conda environments

Segmentation microservice (PyTorch + ML deps)
```bash
conda env create -f car-segmentation-ms/environment-local.yml
```

Backend microservice (no ML deps)
```bash
conda env create -f car-backend-ms/environment-local.yml
```

### Install frontend dependencies

```bash
cd car-frontend && npm install
```

### Run database migrations

```bash
conda activate car-backend-ms
cd car-backend-ms
alembic revision --autogenerate -m "<description>"
alembic upgrade head
```

## Tests

Dev dependencies (pytest, pytest-asyncio, ruff) are included in the conda environments, so no separate install step is needed after `conda env create`.

Backend unit tests:

```bash
conda activate car-backend-ms
cd car-backend-ms
pytest --tb=short -q
```

Frontend unit tests:

```bash
cd car-frontend
npm test
```

Segmentation unit tests use lightweight test doubles for SAM/YOLO so they do not require GPU or model weights:

```bash
conda activate sam-microservice
cd car-segmentation-ms
pytest --tb=short -q
```

Segmentation integration tests run YOLO11n against the reference images in `car-segmentation-ms/input/`. They are skipped automatically when `yolo11n.pt` is absent (CI). To run them locally after placing the weights:

```bash
conda activate sam-microservice
cd car-segmentation-ms
pytest tests/test_input_images_detection.py -v
```

---

## Running All Services

### Open three separate terminals:

Terminal 1 — segmentation MS (port 8000)
```bash
conda activate sam-microservice && cd car-segmentation-ms
uvicorn server:app --reload --port 8000
```

Terminal 2 — backend MS (port 8001)
```bash
conda activate car-backend-ms && cd car-backend-ms
uvicorn main:app --reload --port 8001
```

Terminal 3 — frontend (port 5173)
```bash
cd car-frontend && npm run dev
```

The app is available at **http://localhost:5173**.
