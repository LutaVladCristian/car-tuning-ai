## Project Overview

An AI-powered car image manipulation platform. Users upload car photos, isolate the car or specific parts, and apply AI-driven edits via REST APIs.

**Stack:** Two Python microservices + one React/TypeScript frontend.

## Architecture

```
Browser (car-frontend, port 5173)
    │  JWT in Authorization header
    ▼
car-backend-ms  (port 8001)   ← JWT auth, DB blob storage, photo history
    │
    ▼
car-segmentation-ms  (port 8000)  ← ML inference (YOLO + SAM + OpenAI)
    │
    ▼
PostgreSQL / SQLite
```

## Service Docs

Detailed documentation for each service lives under `.claude/docs/`:

- [car-backend-ms](.claude/docs/car-backend-ms.md) — FastAPI auth gateway, SQLAlchemy, Alembic
- [car-segmentation-ms](.claude/docs/car-segmentation-ms.md) — FastAPI ML inference, YOLO + SAM + OpenAI
- [car-frontend](.claude/docs/car-frontend.md) — React 19 + TypeScript SPA

## Unified Environment Variables

Single `.env` at repo root — source of truth for all three services. See [README.md](../README.md#environment-variables) for setup instructions and `.env.example` for all required variables.

## Running All Services

See [README.md](../README.md#running-all-services) for per-service venv setup and the commands to start all three services.

## Cloud Dev Deployment

See [docs/dev-gcp-architecture.md](../docs/dev-gcp-architecture.md) for the selected GCP dev hosting, CI/CD, auth, and database direction.

## Development Notes

- PR checks run frontend tests plus unit tests for both Python microservices. Segmentation unit tests mock SAM/YOLO import-time dependencies and do not require GPU/model weights.
- `environment-local.yml` in each service directory is the source of truth for local dev dependencies (conda); `requirements.txt` is used by Docker and CI.
- `car-backend-ms` must stay ML-free — heavy deps (torch, ultralytics, etc.) belong only in `car-segmentation-ms`.
- Model weights are gitignored — place in `car-segmentation-ms/model/`: `sam_vit_b_01ec64.pth`, `yolov11seg.pt`, `yolov10n.pt`.
- Do not use plain `pip install` outside of the Conda envs.
- CORS in `car-backend-ms/main.py` is currently hardcoded to `http://localhost:5173` — update `allow_origins` before deploying.
