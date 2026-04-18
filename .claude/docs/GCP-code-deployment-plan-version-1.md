# GCP Deployment Plan — Version 1

**Date:** 2026-04-18  
**Scope:** Docker packaging + Cloud Run deployment for `car-backend-ms` and `car-segmentation-ms`

---

## Architecture Decision

| Service | Runtime | GCP Target |
|---|---|---|
| `car-backend-ms` | Python 3.12, FastAPI, no ML | Cloud Run (CPU) |
| `car-segmentation-ms` | Python 3.10, PyTorch 2.2.0, SAM + YOLO | Cloud Run (GPU — NVIDIA L4) |
| `car-frontend` | React + Vite → nginx | Firebase Hosting |
| Database | PostgreSQL | Cloud SQL |
| Secrets | `OPENAI_API_KEY`, `DATABASE_URL` | Secret Manager |

---

## car-backend-ms/Dockerfile

**Base:** `python:3.12-slim`  
**Port:** `${PORT:-8001}` (Cloud Run injects `PORT` at runtime)  
**Entrypoint:** runs `alembic upgrade head` before uvicorn starts

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD alembic upgrade head && \
    uvicorn main:app --host 0.0.0.0 --port ${PORT:-8001}
```

## car-backend-ms/.dockerignore

```
__pycache__/
*.pyc
*.pyo
tests/
.env
*.db
environment-local.yml
.pytest_cache/
```

---

## car-segmentation-ms/Dockerfile

**Base:** `pytorch/pytorch:2.2.0-cuda11.8-cudnn8-runtime`  
**Port:** `${PORT:-8000}`  
**Why this base:** Ships Python 3.10 + PyTorch 2.2.0 + CUDA 11.8 + cuDNN 8. Cloud Run GPU (NVIDIA L4) is CUDA 12.x hardware but backward-compatible with CUDA 11.8 containers. Torch is pre-installed so we filter it from `requirements.txt` to avoid pip re-fetching the CUDA PyPI variant.  
**Model weights:** baked into the image at build time. Files must be present in `car-segmentation-ms/model/` when building:
- `sam_vit_h_4b8939.pth` (~2.4 GB)
- `yolov11n.pt` (~5 MB)

```dockerfile
FROM pytorch/pytorch:2.2.0-cuda11.8-cudnn8-runtime

WORKDIR /app

# git is required for segment-anything (GitHub install); libgl/libglib for OpenCV headless
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        libglib2.0-0 \
        libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# torch/torchvision/torchaudio already in the base image — install everything else
COPY requirements.txt .
RUN grep -vE "^(torch|torchvision|torchaudio|#|[[:space:]]*$)" requirements.txt \
        > /tmp/requirements-no-torch.txt && \
    pip install --no-cache-dir -r /tmp/requirements-no-torch.txt

COPY server.py segmentation.py utils.py ./

# Bake model weights into the image at build time
COPY model/ ./model/

EXPOSE 8000

CMD uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}
```

## car-segmentation-ms/.dockerignore

```
__pycache__/
*.pyc
*.pyo
tests/
.env
input/
output/
environment-local.yml
.pytest_cache/
```

---

## Cloud Run Environment Variables

These must be injected via Cloud Run service config or Secret Manager — no `.env` file is present in the containers.

**car-backend-ms:**

| Variable | Example value |
|---|---|
| `DATABASE_URL` | `postgresql://user:pass@/car_tuning?host=/cloudsql/PROJECT:REGION:INSTANCE` |
| `SEGMENTATION_MS_URL` | Internal Cloud Run URL of the segmentation service |
| `CORS_ORIGINS` | `["https://your-frontend.web.app"]` |
| `FIREBASE_PROJECT_ID` | Your Firebase project ID |

**car-segmentation-ms:**

| Variable | Source |
|---|---|
| `OPENAI_API_KEY` | Secret Manager |

---

## Build & Deploy Commands

### Build images

```bash
cd car-backend-ms
docker build -t car-backend-ms .

cd ../car-segmentation-ms
docker build -t car-segmentation-ms .
# model files must be present in car-segmentation-ms/model/
```

### Smoke-test locally

```bash
# Backend (needs a live Postgres)
docker run -p 8001:8001 \
  -e DATABASE_URL=postgresql://... \
  -e SEGMENTATION_MS_URL=http://host.docker.internal:8000 \
  car-backend-ms
curl http://localhost:8001/health

# Segmentation
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=sk-... \
  car-segmentation-ms
curl http://localhost:8000/docs
```

### Push to Container Registry

```bash
docker tag car-backend-ms gcr.io/PROJECT/car-backend-ms
docker push gcr.io/PROJECT/car-backend-ms

docker tag car-segmentation-ms gcr.io/PROJECT/car-segmentation-ms
docker push gcr.io/PROJECT/car-segmentation-ms
```

### Deploy to Cloud Run

```bash
# Backend (CPU, no special requirements)
gcloud run deploy car-backend-ms \
  --image gcr.io/PROJECT/car-backend-ms \
  --region REGION \
  --set-env-vars DATABASE_URL=...,SEGMENTATION_MS_URL=...,CORS_ORIGINS=[...]

# Segmentation (GPU — NVIDIA L4; Cloud Run requires min 4 vCPU + 16 GiB with GPU)
gcloud run deploy car-segmentation-ms \
  --image gcr.io/PROJECT/car-segmentation-ms \
  --region REGION \
  --gpu=1 \
  --gpu-type=nvidia-l4 \
  --cpu=4 \
  --memory=16Gi \
  --set-env-vars OPENAI_API_KEY=...
```

> **Note:** Cloud Run GPU is available in select regions: `us-central1`, `us-east4`, `europe-west4`. Confirm availability before deploying.
