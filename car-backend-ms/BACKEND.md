# BACKEND.md — car-backend-ms

## Purpose

`car-backend-ms` is the authenticated API gateway that sits in front of `car-segmentation-ms`. It adds:

- **JWT-based user authentication** (register / login)
- **PostgreSQL persistence** — every uploaded image and its processed result are stored on disk and recorded in the database
- **Photo history API** — users can list and download their past operations
- **Proxy forwarding** — transparently forwards image processing requests to the segmentation MS and returns the results to the caller

The segmentation service (`car-segmentation-ms`) is **not modified** — it remains a stateless internal service.

---

## Architecture

```
Client (HTTP)
    │
    ▼
car-backend-ms  (port 8001)
    │  JWT auth on every protected route
    │  Saves original + result to disk
    │  Records metadata in PostgreSQL
    │
    ├──► car-segmentation-ms  (port 8000)
    │        YOLOv10 + SAM + YOLOv11 + OpenAI
    │
    └──► PostgreSQL (or SQLite for dev)
```

---

## Directory Structure

```
car-backend-ms/
├── main.py                         # FastAPI app factory, router mounts, startup hook
├── config.py                       # pydantic-settings — reads .env into typed Settings
├── dependencies.py                 # Shared FastAPI deps: get_db(), get_current_user()
├── environment.yml                 # Conda environment (Python 3.9, no ML deps)
├── .env                            # Runtime secrets — gitignored
├── .env.example                    # Committed template — copy to .env
├── alembic.ini                     # Alembic migration config
├── alembic/
│   ├── env.py                      # Reads DATABASE_URL from config; registers all models
│   ├── script.py.mako              # Migration file template
│   └── versions/                   # Auto-generated migration scripts
├── storage/                        # Photo files on disk — gitignored
│   └── {user_id}/
│       ├── {uuid}_original.{ext}
│       └── {uuid}_result.png
└── app/
    ├── core/
    │   └── security.py             # bcrypt password hashing + HS256 JWT encode/decode
    ├── db/
    │   ├── base.py                 # SQLAlchemy DeclarativeBase
    │   ├── session.py              # Engine + SessionLocal (auto-detects SQLite vs Postgres)
    │   └── models/
    │       ├── user.py             # User ORM model
    │       └── photo.py            # Photo ORM model + OperationType enum
    ├── schemas/
    │   ├── auth.py                 # RegisterRequest/Response, LoginRequest, TokenResponse
    │   └── photo.py                # PhotoResponse, PhotoListResponse
    ├── routers/
    │   ├── auth.py                 # POST /auth/register, POST /auth/login
    │   ├── segmentation.py         # POST /car-segmentation, /car-part-segmentation, /edit-photo
    │   └── photos.py               # GET /photos, GET /photos/{id}
    └── services/
        ├── proxy_service.py        # httpx async forwarding to segmentation MS
        └── photo_service.py        # Disk I/O helpers (path generation, file save)
```

---

## Database Schema

### `users`

| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | PK, auto-increment |
| username | VARCHAR(50) | UNIQUE, NOT NULL, indexed |
| email | VARCHAR(255) | UNIQUE, NOT NULL, indexed |
| hashed_password | VARCHAR(255) | NOT NULL |
| created_at | TIMESTAMPTZ | server default NOW() |

### `photos`

| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | PK, auto-increment |
| user_id | INTEGER | FK → users.id, NOT NULL, indexed |
| original_filename | VARCHAR(255) | NOT NULL |
| original_file_path | VARCHAR(1024) | NOT NULL |
| result_file_path | VARCHAR(1024) | nullable (null for edit_photo) |
| operation_type | ENUM | `car_segmentation` / `car_part_segmentation` / `edit_photo` |
| operation_params | JSON | nullable — full param dict (e.g. `{"inverse": true}`) |
| created_at | TIMESTAMPTZ | server default NOW() |

---

## Auth Flow

1. `POST /auth/register` — accepts `{username, email, password}` JSON → hashes password with bcrypt → inserts User row → returns `201` with user info.
2. `POST /auth/login` — accepts `{username, password}` JSON → verifies bcrypt hash → returns `200 {"access_token": "eyJ...", "token_type": "bearer"}`.
3. All protected routes require `Authorization: Bearer <token>` header.
4. `get_current_user()` dependency decodes the HS256 JWT → looks up user in DB → returns the `User` ORM object or raises `401`.

JWT payload: `{"sub": "<username>", "exp": <unix timestamp>}`. Expiry configured via `JWT_EXPIRE_MINUTES` in `.env` (default 60 min).

---

## Endpoints

### Auth — `/auth`

| Method | Path | Auth | Request body | Response |
|---|---|---|---|---|
| POST | `/auth/register` | None | JSON `RegisterRequest` | `201 RegisterResponse` |
| POST | `/auth/login` | None | JSON `LoginRequest` | `200 TokenResponse` |

### Segmentation (proxy + persist)

| Method | Path | Auth | Form params | Response |
|---|---|---|---|---|
| POST | `/car-segmentation` | JWT | `file`, `inverse: bool` | `200` PNG stream |
| POST | `/car-part-segmentation` | JWT | `file`, `carPartId: int`, `inverse: bool` | `200` PNG stream |
| POST | `/edit-photo` | JWT | `file`, `prompt: str`, `edit_car: bool`, `size: str` | `200` JSON |

Each segmentation endpoint:
1. Reads uploaded bytes
2. Saves original → `storage/{user_id}/{uuid}_original.{ext}`
3. Forwards to segmentation MS via `httpx` (timeout: 120 s for segmentation, 180 s for edit)
4. Saves result PNG → `storage/{user_id}/{uuid}_result.png`
5. Inserts `Photo` row with paths + params
6. Returns result to caller

### Photos

| Method | Path | Auth | Query params | Response |
|---|---|---|---|---|
| GET | `/photos` | JWT | `skip=0`, `limit=20` | `200 PhotoListResponse` |
| GET | `/photos/{photo_id}` | JWT | — | `200` PNG `FileResponse` |

`GET /photos/{photo_id}` always filters by `user_id` — users cannot access each other's photos.

### Meta

| Method | Path | Auth | Response |
|---|---|---|---|
| GET | `/health` | None | `{"status": "ok"}` |
| GET | `/docs` | None | Swagger UI (Authorize button for JWT built-in) |

---

## Configuration — `.env`

Copy `.env.example` to `.env` and fill in values:

```ini
# PostgreSQL (production):
DATABASE_URL=postgresql://caruser:carpass@localhost:5432/car_tuning_db
# SQLite (local dev, no server needed):
# DATABASE_URL=sqlite:///./car_backend.db

JWT_SECRET_KEY=<random string, 32+ chars>
JWT_EXPIRE_MINUTES=60

SEGMENTATION_MS_URL=http://localhost:8000
STORAGE_BASE_PATH=./storage

APP_HOST=0.0.0.0
APP_PORT=8001
```

---

## Conda Environment

This service uses a **separate, lightweight Conda environment** (`car-backend-ms`) with no ML dependencies (no PyTorch, YOLO, or SAM). This keeps startup fast and the environment portable.

```bash
conda env create -f environment.yml
conda activate car-backend-ms
```

---

## Setup & Running

```bash
# 1. Create and activate env
conda env create -f environment.yml
conda activate car-backend-ms

# 2. Configure secrets
cp .env.example .env
# edit .env

# 3. Generate and apply DB migrations
alembic revision --autogenerate -m "create users and photos tables"
alembic upgrade head

# 4. Start the server (segmentation MS must be on port 8000)
uvicorn main:app --reload --port 8001
```

---

## Running Both Services Together

**Terminal 1 — segmentation MS (port 8000):**
```bash
conda activate sam-microservice
cd car-segmentation-ms
uvicorn server:app --reload --port 8000
```

**Terminal 2 — backend MS (port 8001):**
```bash
conda activate car-backend-ms
cd car-backend-ms
uvicorn main:app --reload --port 8001
```

---

## End-to-End Verification

```bash
# Register
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"secret123"}'

# Login → copy access_token
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"secret123"}'

TOKEN="eyJ..."

# Segment a car (protected)
curl -X POST http://localhost:8001/car-segmentation \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@car.jpg" -F "inverse=false" --output result.png

# List history
curl http://localhost:8001/photos -H "Authorization: Bearer $TOKEN"

# Download a photo
curl http://localhost:8001/photos/1 \
  -H "Authorization: Bearer $TOKEN" --output downloaded.png

# Verify rejection without token
curl http://localhost:8001/photos
# → 401 {"detail":"Not authenticated"}

# Check disk storage
ls storage/1/
# → <uuid>_original.jpg  <uuid>_result.png
```

---

## Key Design Decisions

| Decision | Reason |
|---|---|
| Separate Conda env (no ML deps) | Keeps backend MS lightweight; ML deps live only in `sam-microservice` |
| UUID-prefixed filenames | Avoids chicken-and-egg between DB ID and file path on disk |
| JSON login body (not OAuth2 form) | Consistent API surface — all structured endpoints use JSON |
| `result_file_path` nullable for `edit_photo` | Downstream MS saves result to its own disk; backend cannot intercept the file |
| Ownership filter on `GET /photos/{id}` | Prevents ID-guessing attacks across users |
| SQLite auto-detect in `session.py` | Same codebase works for local dev (SQLite) and production (PostgreSQL) |
