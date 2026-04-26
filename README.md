# Car Tuning AI

An AI-powered car image manipulation platform. Users upload car photos, choose whether to edit the car or the background, and receive AI-edited results.

## Prerequisites

- [Conda](https://docs.conda.io/en/latest/miniconda.html) (Miniconda or Anaconda)
- [Node.js](https://nodejs.org/) v22+
- GPU with CUDA support for practical `car-segmentation-ms` inference; CPU fallback works but is very slow
- Firebase project with Authentication and Storage enabled

## Environment Variables

Copy the template and fill in the required values:

```bash
cp .env.example .env
```

Edit `.env` at the repo root. See `.env.example` for all required variables and descriptions.

## Model Weights

Download and place the following files under `car-segmentation-ms/model/` for local development:

- `sam_vit_h_4b8939.pth` - SAM ViT-H (~2.5 GB)
- `yolov10n.pt` - YOLOv10n COCO car detector (~6 MB)

For deployed segmentation, upload the same filenames to the GCS bucket configured by `MODEL_BUCKET`.

## One-Time Setup

### Create Conda environments

Segmentation microservice (PyTorch + ML deps):

```bash
conda env create -f car-segmentation-ms/environment-local.yml
```

Backend microservice (no ML deps):

```bash
conda env create -f car-backend-ms/environment-local.yml
```

### Install frontend dependencies

```bash
cd car-frontend
npm install
```

### Run database migrations

```bash
conda activate car-backend-ms
cd car-backend-ms
alembic upgrade head
```

## Tests

Dev dependencies are included in the Conda environment files and `package.json`.

Backend unit tests:

```bash
conda activate car-backend-ms
cd car-backend-ms
python -m pytest --tb=short -q
```

Frontend unit tests:

```bash
cd car-frontend
npm test
```

Segmentation tests:

```bash
conda activate sam-microservice
cd car-segmentation-ms
python -m pytest --tb=short -q
```

Most segmentation unit tests use lightweight test doubles for SAM/YOLO. The reference-image detection tests are skipped automatically when `yolov10n.pt` is absent.

To run only the reference-image detection tests after placing the weights:

```bash
conda activate sam-microservice
cd car-segmentation-ms
python -m pytest tests/test_input_images_detection.py -v
```

---

## Running All Services

Open three separate terminals.

Terminal 1 - segmentation MS (port 8000):

```bash
conda activate sam-microservice
cd car-segmentation-ms
uvicorn server:app --reload --port 8000
```

Terminal 2 - backend MS (port 8001):

```bash
conda activate car-backend-ms
cd car-backend-ms
uvicorn main:app --reload --port 8001
```

Terminal 3 - frontend (port 5173):

```bash
cd car-frontend
npm run dev
```

The app is available at **http://localhost:5173**.

## Current Pipeline

`car-segmentation-ms` detects the closest visible car with YOLOv10n (`class 2 = car`), refines that selected box with SAM ViT-H, and writes an OpenAI-compatible mask:

- `edit_car=true`: the closest car is transparent/editable and the background is protected.
- `edit_car=false`: the background is transparent/editable and the closest car is protected.

The backend stores original/result image bytes in Firebase Storage and stores metadata plus Storage paths in PostgreSQL.
