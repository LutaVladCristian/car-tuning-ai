# CLAUDE.md — Car Tuning AI

## Project Overview

An AI-powered car image manipulation platform. Users upload car photos, isolate the car or specific parts (wheels, lights, etc.), and apply AI-driven edits (background replacement, color changes, etc.) via REST APIs.

**Current stage:** Two-service backend — segmentation MS + authenticated backend MS. No frontend yet.

---

## Architecture

Two Python microservices. Clients talk only to `car-backend-ms`; the segmentation MS is an internal service.

```
Client (HTTP)
    │
    ▼
car-backend-ms  (port 8001)   ← JWT auth, DB persistence, photo history
    │
    ▼
car-segmentation-ms  (port 8000)  ← ML inference (YOLO + SAM + OpenAI)
    │
    ▼
PostgreSQL / SQLite
```

```
car-tuning-ai/
├── CLAUDE.md
├── README.md
├── .env                            # OPENAI_API_KEY, WORKING_DIR (for segmentation MS)
├── environment.yml                 # Conda env for car-segmentation-ms (sam-microservice)
├── user_flow_decision_tree.txt    # Product feature planning document
├── car-segmentation-ms/           # ML inference microservice (internal, port 8000)
│   ├── server.py                  # FastAPI app + endpoint definitions
│   ├── SegmentationService.py     # Core CV logic (YOLO + SAM)
│   ├── Utils.py                   # Model init + mask utilities
│   ├── model/                     # Downloaded model weights (gitignored)
│   ├── input/                     # Test images (gitignored)
│   └── output/                    # Generated outputs (gitignored)
└── car-backend-ms/                # Auth + persistence gateway (public-facing, port 8001)
    ├── BACKEND.md                 # Full backend documentation
    ├── main.py
    ├── config.py
    ├── dependencies.py
    ├── environment.yml            # Conda env for car-backend-ms (lightweight, no ML)
    ├── .env.example
    ├── alembic.ini + alembic/
    ├── storage/                   # User photo files on disk (gitignored)
    └── app/
        ├── core/security.py       # bcrypt + JWT
        ├── db/models/             # User, Photo ORM models
        ├── schemas/               # Pydantic I/O schemas
        ├── routers/               # auth, segmentation, photos
        └── services/              # proxy_service, photo_service
```

---

## Tech Stack

### car-segmentation-ms (Conda env: `sam-microservice`)

| Layer | Technology |
|---|---|
| Language | Python 3.9 |
| Web framework | FastAPI + Uvicorn |
| Car detection | YOLOv10n (`yolov10n.pt`) |
| Part segmentation | YOLOv11 seg (`yolov11seg.pt`) |
| Mask generation | SAM ViT-Base (`sam_vit_b_01ec64.pth`) |
| Image I/O | OpenCV, Pillow, NumPy |
| AI editing | OpenAI API (`gpt-image-1`) |
| GPU | PyTorch CUDA (auto-detects GPU/CPU) |

### car-backend-ms (Conda env: `car-backend-ms`)

| Layer | Technology |
|---|---|
| Language | Python 3.9 |
| Web framework | FastAPI + Uvicorn |
| Auth | JWT (HS256) via `python-jose`, bcrypt via `passlib` |
| ORM | SQLAlchemy 2.0 + Alembic migrations |
| Database | PostgreSQL (prod) / SQLite (dev) |
| HTTP proxy | `httpx` async client |
| Config | `pydantic-settings` from `.env` |

---

## Conda Environments

Each service has its own `environment.yml` and Conda env:

| Service | Env name | `environment.yml` location |
|---|---|---|
| `car-segmentation-ms` | `sam-microservice` | `environment.yml` (repo root) |
| `car-backend-ms` | `car-backend-ms` | `car-backend-ms/environment.yml` |

The backend env is **lightweight** — no PyTorch, YOLO, or SAM. Do not merge them.

---

## REST API

### car-segmentation-ms (internal — port 8000, no auth)

| Method | Path | Description |
|---|---|---|
| POST | `/car-segmentation` | Isolate full car from background → PNG |
| POST | `/car-part-segmentation` | Isolate a specific car part by class ID → PNG |
| POST | `/edit-photo` | Replace/edit background using OpenAI → JSON |

### car-backend-ms (public — port 8001, JWT protected)

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | — | Create user account |
| POST | `/auth/login` | — | Get JWT token |
| POST | `/car-segmentation` | JWT | Proxy + save to DB |
| POST | `/car-part-segmentation` | JWT | Proxy + save to DB |
| POST | `/edit-photo` | JWT | Proxy + save to DB |
| GET | `/photos` | JWT | List user's photo history |
| GET | `/photos/{id}` | JWT | Download a photo |
| GET | `/health` | — | Liveness check |

---

## Image Processing Pipeline

1. Client uploads binary image to `car-backend-ms`
2. Backend saves original to `storage/{user_id}/{uuid}_original.{ext}`
3. Proxies request to `car-segmentation-ms` via `httpx`
4. Segmentation MS: YOLOv10 detects car → SAM generates mask → returns RGBA PNG
5. Backend saves result to `storage/{user_id}/{uuid}_result.png`
6. Backend inserts `Photo` row in DB with paths + params
7. Result returned to caller

---

## Running Both Services

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

## First-Time Setup

### car-segmentation-ms
```bash
conda env create -f environment.yml      # root-level environment.yml
conda activate sam-microservice
# Download models into car-segmentation-ms/model/
# Fill in .env (OPENAI_API_KEY, WORKING_DIR)
```

### car-backend-ms
```bash
conda env create -f car-backend-ms/environment.yml
conda activate car-backend-ms
cd car-backend-ms
cp .env.example .env                     # fill in DATABASE_URL, JWT_SECRET_KEY
alembic revision --autogenerate -m "init"
alembic upgrade head
```

---

## Known Issues / Limitations

- **Hardcoded Windows paths** in `car-segmentation-ms/SegmentationService.py` (`working_dir = "C:/Users/..."`) — should be replaced with env var.
- `/edit-photo` result is saved to the segmentation MS's own disk, not proxied back as a file.
- Models are large binary files — gitignored, must be obtained separately.
- No frontend yet.

---

## Planned Features (from `user_flow_decision_tree.txt`)

- MVP: Change car color (mask creation + color-modified generation)
- Spoilers, rims, body kits, lighting modifications
- Background / environment changes (weather, location, lighting style)
- User-drawn masks for custom region selection

---

## Git Branches

- `main` — stable base
- `car-segmentation-ms` — active development branch

---

## Development Notes

- Always consult `car-backend-ms/BACKEND.md` for the full backend design rationale.
- Add new microservices as sibling directories (`car-<name>-ms/`) with their own `environment.yml`.
- Keep model weights out of git — use `model/` with `.gitignore`.
- The `environment.yml` in each service directory is the source of truth for its dependencies — do not use plain `pip install` outside of it.
- `car-backend-ms` env must stay ML-free — heavy deps belong only in `sam-microservice`.
