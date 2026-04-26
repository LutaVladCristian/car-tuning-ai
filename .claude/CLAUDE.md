## Project Overview

An AI-powered car image manipulation platform. Users upload car photos, choose whether to edit the car or the background, and receive AI-edited images via REST APIs.

**Stack:** Two Python microservices plus one React/TypeScript frontend.

## Architecture

```
+-----------------------------------------------------+
|                    Browser                          |
|              http://localhost:5173                  |
|           React 19 + TypeScript (Vite)              |
+----------------------+------------------------------+
                       |  HTTP (Axios + Firebase ID token)
                       v
+-----------------------------------------------------+
|            car-backend-ms  :8001                    |
|         FastAPI - auth gateway + proxy              |
|   Firebase auth - SQLAlchemy ORM - Alembic          |
+-------+------------------------------+--------------+
        |  SQL (psycopg2)              |  HTTP (httpx)
        v                              v
+--------------+   +---------------------------------+
|  PostgreSQL  |   |     car-segmentation-ms  :8000  |
|  (Cloud SQL  |   |  FastAPI - ML inference          |
|   or local)  |   |  YOLOv10n - SAM ViT-H - OpenAI   |
+--------------+   +---------------------------------+
        |
        v
+--------------+
| Firebase     |
| Storage      |
+--------------+
```

**Request flow:**
1. Browser authenticates with Firebase and sends image + form data to `car-backend-ms`.
2. Backend verifies the Firebase ID token, validates the upload, and proxies the request to `car-segmentation-ms`.
3. Segmentation service detects the closest car with YOLOv10n, refines its mask with SAM, calls OpenAI for `/edit-photo`, and returns base64 result/mask PNGs.
4. Backend stores the original, result, and mask images in Firebase Storage, stores paths/metadata in PostgreSQL, and returns the result PNG to the browser.
5. Frontend displays the saved original/result pair in an interactive comparison slider; history selections load their pair into the same slider.

## Service Docs

Detailed documentation for each service lives under `.claude/docs/`:

- [car-backend-ms](/.claude/docs/car-backend-ms.md) - FastAPI auth gateway, SQLAlchemy, Alembic, Firebase Storage
- [car-segmentation-ms](/.claude/docs/car-segmentation-ms.md) - FastAPI ML inference, YOLOv10n, SAM, OpenAI
- [car-frontend](/.claude/docs/car-frontend.md) - React 19 + TypeScript SPA

## Unified Environment Variables

Single `.env` at repo root - source of truth for all three services. See [README.md](../README.md#environment-variables) for setup instructions and `.env.example` for all required variables.

## Running All Services

See [README.md](../README.md#running-all-services) for per-service Conda environments, setup, and the commands to start all three services.

## GitHub Actions

Two workflows live in `.github/workflows/`:

- `pr-checks.yml` - runs on pull requests and pushes to `main`: secret scan, backend/frontend/segmentation lint, tests, builds, and dependency audits.
- `deploy.yml` - runs when a pull request into `main` is closed as merged: builds Docker images, pushes to GCR, deploys backend and segmentation to Cloud Run, and deploys the frontend to Firebase Hosting.

## GCP Deployment Notes

React + TypeScript frontend -> Firebase Hosting
Python backend API -> Cloud Run
Python segmentation microservice -> Cloud Run with GPU
Persistent database -> Cloud SQL for PostgreSQL
Photo image storage -> Firebase Storage
User authentication -> Firebase Authentication / Identity Platform with Google Sign-In
API keys / model secrets -> Secret Manager
Model weights -> GCS model bucket

## Development Notes

- `environment-local.yml` in each service directory is the source of truth for local Conda dependencies.
- `car-backend-ms` must stay ML-free; heavy dependencies such as torch, ultralytics, and segment-anything belong only in `car-segmentation-ms`.
- Model weights are gitignored. Place these in `car-segmentation-ms/model/`: `sam_vit_h_4b8939.pth`, `yolov10n.pt`.
- Do not use plain `pip install` outside of the Conda envs for local development.
- CORS origins are configured via `CORS_ORIGINS` as a JSON list. Production value: `["https://slick-tunes.web.app"]`; local default: `["http://localhost:5173"]`.
