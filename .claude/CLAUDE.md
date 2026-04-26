## Project Overview

An AI-powered car image manipulation platform. Users upload car photos, isolate the car or specific parts, and apply AI-driven edits via REST APIs.

**Stack:** Two Python microservices + one React/TypeScript frontend.

## Architecture

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                    Browser                          â”‚
â”‚              http://localhost:5173                  â”‚
â”‚           React 19 + TypeScript (Vite)              â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                       â”‚ HTTP (Axios + Firebase ID token)
                       â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚            car-backend-ms  :8001                    â”‚
â”‚         FastAPI â€” auth gateway + proxy              â”‚
â”‚   Firebase auth Â· SQLAlchemy ORM Â· Alembic migrations    â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
        â”‚ SQL (psycopg2)           â”‚ HTTP (httpx)
        â–¼                         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  PostgreSQL   â”‚   â”‚     car-segmentation-ms  :8000  â”‚
â”‚  (Cloud SQL   â”‚   â”‚  FastAPI â€” ML inference          â”‚
â”‚   or local)   â”‚   â”‚  YOLO11n Â· SAM ViT-H Â· OpenAI  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

**Request flow:**
1. Browser authenticates and sends image + form data to `car-backend-ms`.
2. Backend verifies Firebase ID token, stores the original image in PostgreSQL, then proxies the request to `car-segmentation-ms`.
3. Segmentation service runs YOLO â†’ SAM (â†’ OpenAI for `/edit-photo`) and returns a PNG.
4. Backend stores the result PNG in PostgreSQL and returns it to the browser.

## Service Docs

Detailed documentation for each service lives under `.claude/docs/`:

- [car-backend-ms](/.claude/docs/car-backend-ms.md) â€” FastAPI auth gateway, SQLAlchemy, Alembic
- [car-segmentation-ms](/.claude/docs/car-segmentation-ms.md) â€” FastAPI ML inference, YOLO + SAM + OpenAI
- [car-frontend](/.claude/docs/car-frontend.md) â€” React 19 + TypeScript SPA

## Unified Environment Variables

Single `.env` at repo root â€” source of truth for all three services. See [README.md](../README.md#environment-variables) for setup instructions and `.env.example` for all required variables.

## Running All Services

See [README.md](../README.md#create-conda-environments) for per-service Conda environments, setup and the commands to start all three services.

## GitHub Actions

Two workflows live in `.github/workflows/`:

- `pr-checks.yml` â€” runs on pull requests: backend/frontend/segmentation unit tests, lint/build, Alembic migration check against Postgres.
- `deploy.yml` â€” runs on push to `main` or `main-to-deploy-version-3`: builds Docker images, pushes to GCR, deploys all three services to Cloud Run / Firebase Hosting.

## Deploying on GCP considerations (prone to improvements)

React + TypeScript frontend â†’ Firebase Hosting  
Python backend API â†’ Cloud Run  
Python microservice â†’ Cloud Run  
Persistent database â†’ Cloud SQL for PostgreSQL  
User authentication â†’ Firebase Authentication / Identity   Platform with Google Sign-In  
API keys / model secrets â†’ Secret Manager

## Development Notes

- PR checks run frontend tests plus unit tests for both Python microservices.
- `environment-local.yml` in each service directory is the source of truth for local dev dependencies (conda);
- `car-backend-ms` must stay ML-free â€” heavy deps (torch, ultralytics, etc.) belong only in `car-segmentation-ms`.
- Model weights are gitignored â€” place in `car-segmentation-ms/model/`: `sam_vit_h_4b8939.pth`, `yolo11n.pt`.
- Do not use plain `pip install` outside of the Conda envs.
- CORS origins are configured via the `CORS_ORIGINS` env var (JSON list). Production value: `["https://slick-tunes.web.app"]`; local default: `["http://localhost:5173"]`.
