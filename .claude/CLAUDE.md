# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

Single `.env` at repo root — source of truth for all three services.

```ini
# car-segmentation-ms
OPENAI_API_KEY=

# car-backend-ms
DATABASE_URL=sqlite:///./car_backend.db
JWT_SECRET_KEY=change-me-to-32-plus-chars
JWT_EXPIRE_MINUTES=60
SEGMENTATION_MS_URL=http://localhost:8000
APP_HOST=0.0.0.0
APP_PORT=8001

# car-frontend (read via vite.config.ts envDir: '..')
VITE_API_BASE_URL=http://localhost:8001
```

## Running All Services

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

## Development Notes

- `car-backend-ms` Conda env must stay ML-free — heavy deps belong only in `sam-microservice`.
- `environment-local.yml` in each service directory is the source of truth for its dependencies.
- Model weights are gitignored — place in `car-segmentation-ms/model/`: `sam_vit_b_01ec64.pth`, `yolov11seg.pt`, `yolov10n.pt`.
- Do not use plain `pip install` outside of the Conda envs.
- CORS in `car-backend-ms/main.py` is currently hardcoded to `http://localhost:5173` — update `allow_origins` before deploying.
