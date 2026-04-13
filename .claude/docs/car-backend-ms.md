# car-backend-ms

FastAPI gateway service — JWT auth, photo persistence, and proxy to `car-segmentation-ms`.

**Conda env:** `car-backend-ms` (Python 3.12, no ML deps)
**Port:** 8001
**Config:** `pydantic-settings` reads `../.env` (repo root) via `env_file = "../.env"`

## Commands

```bash
conda activate car-backend-ms
cd car-backend-ms

uvicorn main:app --reload --port 8001   # dev server

# Migrations
alembic revision --autogenerate -m "<description>"
alembic upgrade head
alembic downgrade -1
```

Unit tests live under `car-backend-ms/tests/`.

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest --tb=short -q
```

PR checks run the backend unit tests against a real Postgres service after `alembic upgrade head` and `alembic check`.

## Structure

```
car-backend-ms/
├── main.py               # FastAPI app, CORS middleware, router registration
├── config.py             # Settings (pydantic-settings), get_settings() cached with lru_cache
├── dependencies.py       # get_db() session generator, get_current_user() JWT dependency
├── environment-local.yml # Conda env definition (source of truth for deps)
├── alembic.ini
├── alembic/versions/     # DB migration scripts
└── app/
    ├── core/security.py          # hash_password, verify_password, create_access_token, decode_access_token
    ├── db/
    │   ├── session.py            # SessionLocal (SQLAlchemy engine + session factory)
    │   ├── base.py               # declarative Base
    │   └── models/               # User, Photo ORM models
    ├── schemas/                  # Pydantic request/response models (auth.py, photo.py)
    ├── routers/                  # auth.py, segmentation.py, photos.py
    └── services/
        └── proxy_service.py      # httpx async forwarding to segmentation MS
```

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | — | Create user (bcrypt hash, 201) |
| POST | `/auth/login` | — | Returns JWT bearer token |
| POST | `/car-segmentation` | JWT | Proxy + store blobs in DB |
| POST | `/car-part-segmentation` | JWT | Proxy + store blobs in DB |
| POST | `/edit-photo` | JWT | Proxy + store original blob in DB |
| GET | `/photos` | JWT | List user's photo history (metadata only) |
| GET | `/photos/{id}` | JWT | Stream photo blob as image/png |
| GET | `/health` | — | Liveness check |

## Auth Flow

1. `POST /auth/register` → bcrypt hash → User row → 201
2. `POST /auth/login` → verify hash → `{"access_token": "eyJ...", "token_type": "bearer"}`
3. Protected routes: `Authorization: Bearer <token>`
4. `get_current_user()` in `dependencies.py` decodes HS256 JWT → DB lookup → User ORM or 401

JWT payload: `{"sub": "<username>", "exp": <unix>}`. Expiry via `JWT_EXPIRE_MINUTES`.

## Database Schema

### `users`
| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | PK |
| username | VARCHAR(50) | UNIQUE, NOT NULL, indexed |
| email | VARCHAR(255) | UNIQUE, NOT NULL, indexed |
| hashed_password | VARCHAR(255) | NOT NULL |
| created_at | TIMESTAMPTZ | server default NOW() |

### `photos`
| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | PK |
| user_id | INTEGER | FK → users.id, indexed |
| original_filename | VARCHAR(255) | NOT NULL |
| original_image | BYTEA/BLOB | NOT NULL |
| result_image | BYTEA/BLOB | nullable |
| operation_type | ENUM | `car_segmentation` / `car_part_segmentation` / `edit_photo` |
| operation_params | JSON | nullable |
| created_at | TIMESTAMPTZ | server default NOW() |

## Proxy Timeouts

- `/car-segmentation`, `/car-part-segmentation`: 120 s (`proxy_service.py`)
- `/edit-photo`: 180 s (OpenAI image generation)

## Docker

```bash
docker build -t car-backend-ms ./car-backend-ms
docker run -p 8001:8001 \
  -e DATABASE_URL=postgresql://user:pass@host/db \
  -e JWT_SECRET_KEY=secret \
  -e SEGMENTATION_MS_URL=http://segmentation-host:8000 \
  car-backend-ms
```

The Docker image uses `python:3.12-slim` with `pip install` (no Conda on container runtimes).
