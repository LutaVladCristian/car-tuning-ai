# car-backend-ms

FastAPI gateway service — JWT auth, photo persistence, and proxy to `car-segmentation-ms`.

**Conda env:** `car-backend-ms` (Python 3.12, no ML deps)
**Port:** 8001
**Config:** `pydantic-settings` reads `../.env` (repo root) via `env_file = "../.env"`

## Commands

See [README.md](../../README.md) for commands.

## Structure

```

```

## API Endpoints


## Auth Flow


## Database Schema


## Proxy Timeouts

- `/car-segmentation`, `/car-part-segmentation`: 120 s (`proxy_service.py`)
- `/edit-photo`: 180 s (OpenAI image generation)