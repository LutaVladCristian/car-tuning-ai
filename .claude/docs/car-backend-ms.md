# car-backend-ms

FastAPI gateway service — JWT auth, photo persistence, and proxy to `car-segmentation-ms`.

**Conda env:** `car-backend-ms` (Python 3.12, no ML deps)
**Port:** 8001
**Config:** `pydantic-settings` reads `../.env` (repo root) via `env_file = "../.env"`

## Commands

See [README.md](../../README.md) for commands.

## Structure

```
car-backend-ms/
├── main.py                    # FastAPI app, CORS, router registration, GET /health
├── config.py                  # pydantic-settings reads ../.env
├── dependencies.py            # JWT decode + DB session FastAPI dependencies
├── alembic/
│   └── versions/
│       └── 45e90066957a_db_setup_v1.py  # initial migration (users + photos tables)
└── app/
    ├── core/
    │   └── security.py        # bcrypt hashing, JWT create/decode (python-jose)
    ├── db/
    │   ├── session.py         # SQLAlchemy engine + SessionLocal
    │   ├── base.py            # declarative Base
    │   └── models/
    │       ├── user.py        # User ORM
    │       └── photo.py       # Photo ORM + OperationType enum
    ├── routers/
    │   ├── auth.py            # POST /auth/register, POST /auth/login
    │   ├── photos.py          # GET /photos, GET /photos/{id}
    │   └── segmentation.py    # POST /car-segmentation, /car-part-segmentation, /edit-photo
    ├── schemas/               # Pydantic request/response models
    └── services/
        └── proxy_service.py   # httpx forwarding to car-segmentation-ms
```

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | None | Health check |
| POST | `/auth/register` | None | Create user account |
| POST | `/auth/login` | None | Returns JWT access token |
| GET | `/photos` | JWT | List user's photos with pagination (`skip`, `limit`) — returns `{photos, total}` |
| GET | `/photos/{photo_id}` | JWT | Stream photo PNG (result image if available, otherwise original) |
| POST | `/car-segmentation` | JWT | Proxy to segmentation MS (120 s timeout); saves Photo record |
| POST | `/car-part-segmentation` | JWT | Proxy to segmentation MS (120 s timeout); saves Photo with `carPartId` |
| POST | `/edit-photo` | JWT | Proxy to segmentation MS (180 s timeout for OpenAI); saves Photo with `prompt` |

## Auth Flow

1. **Register** — `POST /auth/register` validates uniqueness of `username` and `email`, hashes the password with bcrypt, and inserts a `User` row.
2. **Login** — `POST /auth/login` loads the user by username, verifies the bcrypt hash, and returns a signed JWT with claim `{"sub": username}`.
3. **Protected endpoints** — `dependencies.py` extracts `Authorization: Bearer <token>`, decodes the JWT via `python-jose`, and resolves the `User` from the DB. A missing or invalid token returns HTTP 401.

## Database Schema

**`users` table**

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | integer | PK, auto-increment |
| `username` | varchar | unique, not null |
| `email` | varchar | unique, not null |
| `hashed_password` | varchar | not null |
| `created_at` | timestamp | default now() |

**`photos` table**

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | integer | PK, auto-increment |
| `user_id` | integer | FK → users.id, not null |
| `original_filename` | varchar | |
| `original_image` | LargeBinary | raw bytes of uploaded file |
| `result_image` | LargeBinary | nullable — filled after ML processing |
| `operation_type` | enum | `car_segmentation` \| `car_part_segmentation` \| `edit_photo` |
| `operation_params` | JSON | extra params: `carPartId`, `prompt`, `edit_car`, `inverse`, `size` |
| `created_at` | timestamp | default now() |

Both tables are created by the single Alembic migration `alembic/versions/45e90066957a_db_setup_v1.py`.


## Proxy Timeouts

- `/car-segmentation`, `/car-part-segmentation`: 120 s (`proxy_service.py`)
- `/edit-photo`: 180 s (OpenAI image generation)