# car-backend-ms

FastAPI gateway service — Firebase auth, photo persistence, and proxy to `car-segmentation-ms`.

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
├── dependencies.py            # Firebase token verification + DB session FastAPI dependencies
├── alembic/
│   └── versions/
│       └── 45e90066957a_db_setup_v1.py  # initial migration (users + photos tables)
└── app/
    ├── core/
    │   └── security.py        # Firebase ID token verification (firebase-admin)
    ├── db/
    │   ├── session.py         # SQLAlchemy engine + SessionLocal
    │   ├── base.py            # declarative Base
    │   └── models/
    │       ├── user.py        # User ORM
    │       └── photo.py       # Photo ORM + OperationType enum
    ├── routers/
    │   ├── auth.py            # POST /auth/firebase
    │   ├── photos.py          # GET /photos, GET /photos/{id}
    │   └── segmentation.py    # POST /edit-photo
    ├── schemas/               # Pydantic request/response models
    └── services/
        └── proxy_service.py   # httpx forwarding to car-segmentation-ms
```

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | None | Health check |
| POST | `/auth/firebase` | None | Exchange Firebase ID token for synced user record |
| GET | `/photos` | Bearer | List user's photos with pagination (`skip`, `limit`) — returns `{photos, total}` |
| GET | `/photos/{photo_id}` | Bearer | Stream photo PNG (result image if available, otherwise original) |
| POST | `/edit-photo` | Bearer | Proxy to segmentation MS (180 s timeout for OpenAI); saves Photo record |

## Auth Flow

1. **Google Sign-In** — browser calls Firebase; Firebase returns a short-lived ID token.
2. **Sync user** — `POST /auth/firebase` receives `{id_token}`, calls `verify_firebase_token()` (firebase-admin SDK), upserts a `User` row (keyed on `firebase_uid`), and returns the backend user record.
3. **Protected endpoints** — `dependencies.py` extracts `Authorization: Bearer <token>`, calls `verify_firebase_token()`, and resolves the `User` from the DB. A missing or invalid token returns HTTP 401.

## Database Schema

**`users` table**

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | integer | PK, auto-increment |
| `firebase_uid` | varchar(128) | unique, not null, indexed |
| `email` | varchar(255) | unique, not null |
| `display_name` | varchar(255) | nullable |
| `created_at` | timestamp | default now() |

**`photos` table**

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | integer | PK, auto-increment |
| `user_id` | integer | FK → users.id, not null |
| `original_filename` | varchar | |
| `original_image` | LargeBinary | raw bytes of uploaded file |
| `result_image` | LargeBinary | nullable — filled after ML processing |
| `operation_type` | enum | `edit_photo` |
| `operation_params` | JSON | extra params: `carPartId`, `prompt`, `edit_car`, `inverse`, `size` |
| `created_at` | timestamp | default now() |

Two Alembic migrations: `45e90066957a_db_setup_v1.py` (initial tables) and `c1d2e3f4a5b6_firebase_auth_v2.py` (Firebase auth columns + enum narrowing).


## Proxy Timeouts

- `/edit-photo`: 180 s (OpenAI image generation)