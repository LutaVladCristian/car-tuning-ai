## Project Overview

An AI-powered car image manipulation platform. Users upload car photos, isolate the car or specific parts, and apply AI-driven edits via REST APIs.

**Stack:** Two Python microservices + one React/TypeScript frontend.

## Architecture

```

```

## Service Docs

Detailed documentation for each service lives under `.claude/docs/`:

- [car-backend-ms](/.claude/docs/car-backend-ms.md) — FastAPI auth gateway, SQLAlchemy, Alembic
- [car-segmentation-ms](/.claude/docs/car-segmentation-ms.md) — FastAPI ML inference, YOLO + SAM + OpenAI
- [car-frontend](/.claude/docs/car-frontend.md) — React 19 + TypeScript SPA

## Unified Environment Variables

Single `.env` at repo root — source of truth for all three services. See [README.md](../README.md#environment-variables) for setup instructions and `.env.example` for all required variables.

## Running All Services

See [README.md](../README.md#create-conda-environments) for per-service Conda environments, setup and the commands to start all three services.

## GitHub Actions

PR checks run backend, frontend, and segmentation unit-test suites, lint/build, backend Alembic migration checks against Postgres. The workflow directory is intentionally limited to:

- `.github/workflows/pr-checks.yml` for pull-request checks.

## Deploying on GCP considerations (prone to improvements)

React + TypeScript frontend → Firebase Hosting  
Python backend API → Cloud Run  
Python microservice → Cloud Run  
Persistent database → Cloud SQL for PostgreSQL  
User authentication → Firebase Authentication / Identity   Platform with Google Sign-In  
API keys / model secrets → Secret Manager

## Development Notes

- PR checks run frontend tests plus unit tests for both Python microservices.
- `environment-local.yml` in each service directory is the source of truth for local dev dependencies (conda);
- `car-backend-ms` must stay ML-free — heavy deps (torch, ultralytics, etc.) belong only in `car-segmentation-ms`.
- Model weights are gitignored — place in `car-segmentation-ms/model/`: `sam_vit_b_01ec64.pth`, `yolov11seg.pt`, `yolov10n.pt`.
- Do not use plain `pip install` outside of the Conda envs.
- CORS in `car-backend-ms/main.py` is currently hardcoded to `http://localhost:5173` — update `allow_origins` before deploying.
