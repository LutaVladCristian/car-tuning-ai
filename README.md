# Car Tuning AI

An AI-powered car image manipulation platform. Users upload car photos, isolate the car or specific parts, and apply AI-driven edits.

## Prerequisites

- [Conda](https://docs.conda.io/en/latest/miniconda.html) (Miniconda or Anaconda)
- [Node.js](https://nodejs.org/) v18+
- GPU with CUDA support (required for ML inference; CPU fallback is very slow)

## One-time Setup

### 1. Environment variables

Copy the template and fill in the required values:

```bash
cp .env.example .env
```

Edit `.env` at the repo root:

```ini
# car-segmentation-ms
OPENAI_API_KEY=sk-...
WORKING_DIR=/absolute/path/to/car-segmentation-ms

# car-backend-ms
DATABASE_URL=sqlite:///./car_backend.db
JWT_SECRET_KEY=change-me-to-32-plus-chars
JWT_EXPIRE_MINUTES=60
SEGMENTATION_MS_URL=http://localhost:8000
APP_HOST=0.0.0.0
APP_PORT=8001

# car-frontend
VITE_API_BASE_URL=http://localhost:8001
```

### 2. Model weights

Download and place the following files under `car-segmentation-ms/model/`:

- `sam_vit_b_01ec64.pth` — SAM ViT-Base
- `yolov11seg.pt` — YOLOv11 segmentation (car part detection)
- `yolov10n.pt` — YOLOv10n (full car detection)

### 3. Create Conda environments

```bash
# Segmentation microservice (PyTorch + ML deps)
conda env create -f car-segmentation-ms/environment-local.yml

# Backend microservice (no ML deps)
conda env create -f car-backend-ms/environment-local.yml
```

### 4. Install frontend dependencies

```bash
cd car-frontend && npm install
```

### 5. Run database migrations

```bash
conda activate car-backend-ms
cd car-backend-ms
alembic upgrade head
```

---

## Running on local machine all services

Open three separate terminals:

```bash
# Terminal 1 — segmentation MS (port 8000)
conda activate sam-microservice && cd car-segmentation-ms
uvicorn server:app --reload --port 8000

# Terminal 2 — backend MS (port 8001)
conda activate car-backend-ms && cd car-backend-ms
uvicorn main:app --reload --port 8001

# Terminal 3 — frontend (port 5173)
cd car-frontend && npm run dev
```

The app is available at **http://localhost:5173**.
