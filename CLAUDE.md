# CLAUDE.md — Car Tuning AI

## Project Overview

An AI-powered car image manipulation platform. Users upload car photos, isolate the car or specific parts (wheels, lights, etc.), and apply AI-driven edits (background replacement, color changes, etc.) via REST APIs.

**Stack:** Two Python microservices (segmentation + backend) + one React/TypeScript frontend.

---

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

```
car-tuning-ai/
├── .env                            # Unified secrets for all three services (gitignored)
├── user_flow_decision_tree.txt     # Product feature planning document
├── car-segmentation-ms/            # ML inference microservice (internal, port 8000)
│   ├── server.py                   # FastAPI app + endpoint definitions
│   ├── SegmentationService.py      # Core CV logic (YOLO + SAM)
│   ├── Utils.py                    # Model init + mask utilities
│   ├── environment.yml             # Conda env: sam-microservice
│   ├── model/                      # Downloaded model weights (gitignored)
│   ├── input/                      # Test images (gitignored)
│   └── output/                     # Generated outputs (gitignored)
└── car-backend-ms/                 # Auth + persistence gateway (public-facing, port 8001)
│   ├── main.py
│   ├── config.py                   # pydantic-settings — reads ../.env into typed Settings
│   ├── dependencies.py
│   ├── environment.yml             # Conda env: car-backend-ms (no ML deps)
│   ├── alembic.ini + alembic/
│   └── app/
│       ├── core/security.py        # bcrypt + JWT
│       ├── db/models/              # User, Photo ORM models (images as DB blobs)
│       ├── schemas/                # Pydantic I/O schemas
│       ├── routers/                # auth, segmentation, photos
│       └── services/
│           └── proxy_service.py    # httpx forwarding to segmentation MS
└── car-frontend/                   # React + TypeScript SPA (port 5173)
    ├── vite.config.ts              # envDir: '..' — reads VITE_* from root .env
    ├── tailwind.config.js
    └── src/
        ├── api/                    # Axios client + auth/photos/segmentation API calls
        ├── context/AuthContext.tsx # JWT auth state + localStorage persistence
        ├── hooks/                  # usePhotoHistory, useEditPhoto
        ├── lib/promptBuilder.ts    # TuningFormState → natural language prompt
        ├── pages/                  # LoginPage, SignUpPage, TuningPage
        └── components/             # layout, auth, tuning panels, results
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
| Image storage | Binary blobs in DB (`LargeBinary` column) |
| HTTP proxy | `httpx` async client |
| Config | `pydantic-settings` reads `../.env` (repo root) |

### car-frontend

| Concern | Choice |
|---|---|
| Bundler | Vite 5 |
| UI | React 18 + TypeScript 5 |
| Routing | React Router v6 |
| HTTP | Axios (with JWT interceptor) |
| Styling | Tailwind CSS v3 |
| State | React Context + useReducer |

---

## Unified Environment Variables

Single `.env` at repo root — source of truth for all three services.

```ini
# ─── car-segmentation-ms ───────────────────────────────────────────────────
OPENAI_API_KEY=your-openai-api-key-here
WORKING_DIR=/absolute/path/to/car-tuning-ai/car-segmentation-ms

# ─── car-backend-ms ────────────────────────────────────────────────────────
DATABASE_URL=sqlite:///./car_backend.db          # dev; use postgresql:// for prod
JWT_SECRET_KEY=change-me-to-a-random-32-plus-char-secret
JWT_EXPIRE_MINUTES=60
SEGMENTATION_MS_URL=http://localhost:8000
APP_HOST=0.0.0.0
APP_PORT=8001

# ─── car-frontend ──────────────────────────────────────────────────────────
# Vite reads from car-frontend/.env — keep that file in sync with this value.
VITE_API_BASE_URL=http://localhost:8001
```

**How each service loads it:**
- `car-segmentation-ms` — `load_dotenv(find_dotenv())` in `SegmentationService.py` walks up to find root `.env`
- `car-backend-ms` — `pydantic-settings` reads `env_file = "../.env"` (relative to the service dir)
- `car-frontend` — `vite.config.ts` sets `envDir: '..'`, so Vite reads `VITE_*` vars directly from the root `.env`

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
| POST | `/car-segmentation` | JWT | Proxy + store blobs in DB |
| POST | `/car-part-segmentation` | JWT | Proxy + store blobs in DB |
| POST | `/edit-photo` | JWT | Proxy + store original blob in DB |
| GET | `/photos` | JWT | List user's photo history (metadata) |
| GET | `/photos/{id}` | JWT | Stream photo from DB blob |
| GET | `/health` | — | Liveness check |

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
| original_image | BYTEA/BLOB | NOT NULL — raw bytes of the uploaded image |
| result_image | BYTEA/BLOB | nullable — null for `edit_photo` operations |
| operation_type | ENUM | `car_segmentation` / `car_part_segmentation` / `edit_photo` |
| operation_params | JSON | nullable — e.g. `{"inverse": true}` |
| created_at | TIMESTAMPTZ | server default NOW() |

---

## Auth Flow

1. `POST /auth/register` → bcrypt hash → insert User row → `201`
2. `POST /auth/login` → verify hash → return `{"access_token": "eyJ...", "token_type": "bearer"}`
3. All protected routes require `Authorization: Bearer <token>`
4. `get_current_user()` decodes HS256 JWT → DB lookup → `User` ORM or `401`

JWT payload: `{"sub": "<username>", "exp": <unix timestamp>}`. Expiry via `JWT_EXPIRE_MINUTES`.

---

## Frontend

### Routes

| Path | Component | Auth |
|---|---|---|
| `/login` | LoginPage | Public |
| `/signup` | SignUpPage | Public |
| `/` | TuningPage (inside AppShell) | Protected (JWT required) |
| `/*` | Redirect to `/` | — |

### Tuning Page Architecture

```
TuningPage (useReducer → TuningFormState)
├── ImageSelector        — upload file OR pick from GET /photos history
├── TuningForm           — dispatches TuningAction to reducer
│   ├── TargetSelector   — "Edit Car" / "Edit Background"
│   ├── [Car mode]
│   │   ├── ColorPicker  — swatches + text + finish (solid/metallic/matte/special)
│   │   ├── BodyModPanel — spoiler, rims, body kit, stance
│   │   └── CosmeticPanel— window tint, lighting, vinyl wrap
│   └── [Background mode]
│       ├── EnvironmentPicker — urban/mountain/track/beach/industrial
│       ├── TimePicker        — day/sunset/night/dawn
│       ├── WeatherPicker     — clear/rain/snow/fog
│       └── StylePicker       — static/action/three-quarter/dramatic
├── PromptPreview        — live preview of assembled prompt; manually editable
├── Submit button        → useEditPhoto.submit()
├── ResultDisplay        — status machine: idle/submitting/polling/success/error
└── PhotoHistoryPanel    — paginated history; click to reuse photo as input
```

### Prompt Builder (`src/lib/promptBuilder.ts`)

Pure function `buildPrompt(form: TuningFormState): string`. Assembles a natural-language OpenAI prompt from the form state. If `customPromptOverride !== null`, returns that string directly.

### edit-photo polling flow

1. Submit → snapshot `GET /photos` total count
2. `POST /edit-photo` (up to 180 s timeout, OpenAI processes)
3. Poll `GET /photos?limit=1` until `total` increases
4. Retrieve new `photo.id` → `GET /photos/{id}` → display result

### Design tokens (dark automotive theme)

| Token | Value |
|---|---|
| `surface-900` | `#0A0A0A` — page background |
| `surface-800` | `#111111` — card/panel |
| `surface-700` | `#1C1C1E` — inputs |
| `surface-600` | `#2C2C2E` — borders |
| `accent-blue` | `#3B82F6` — "Edit Car" mode |
| `accent-orange` | `#F97316` — "Edit Background" mode |

---

## Running All Three Services

```bash
# Terminal 1 — segmentation MS (port 8000)
conda activate sam-microservice
cd car-segmentation-ms
uvicorn server:app --reload --port 8000

# Terminal 2 — backend MS (port 8001)
conda activate car-backend-ms
cd car-backend-ms
uvicorn main:app --reload --port 8001

# Terminal 3 — frontend (port 5173)
cd car-frontend
npm run dev
```

---

## First-Time Setup

### car-segmentation-ms
```bash
conda env create -f car-segmentation-ms/environment.yml
conda activate sam-microservice
# Download model weights into car-segmentation-ms/model/:
#   sam_vit_b_01ec64.pth, yolov11seg.pt, yolov10n.pt
cp .env.example .env   # set OPENAI_API_KEY and WORKING_DIR
```

### car-backend-ms
```bash
conda env create -f car-backend-ms/environment.yml
conda activate car-backend-ms
cd car-backend-ms
# .env is read from ../.env (repo root) — fill in DATABASE_URL and JWT_SECRET_KEY
alembic revision --autogenerate -m "init"
alembic upgrade head
```

### car-frontend
```bash
cd car-frontend
npm install
# VITE_API_BASE_URL is read from the root .env via vite.config.ts (envDir: '..')
npm run dev
```

---

## GCP Deployment

| Component | GCP Service |
|---|---|
| `car-segmentation-ms` | Compute Engine GPU VM (n1-standard-4 + T4) — heavy ML deps |
| `car-backend-ms` | Cloud Run — lightweight, stateless |
| PostgreSQL | Cloud SQL (Postgres 15) |
| `car-frontend` | Firebase Hosting (static SPA) |
| Secrets | Secret Manager (OPENAI_API_KEY, JWT_SECRET_KEY, DATABASE_URL) |
| Images | Artifact Registry |

Key steps:
- `car-backend-ms` Dockerfile uses `pip install` (no Conda on Cloud Run); see `environment.yml` for the dep list
- Set `SEGMENTATION_MS_URL` to the VM's internal IP — keep segmentation MS off the public internet
- Run `alembic upgrade head` via Cloud SQL Auth Proxy before first deploy
- Set `VITE_API_BASE_URL` to the Cloud Run URL before `npm run build`, then `firebase deploy`

---

## Notes

- Model weights are large binaries — gitignored, must be obtained separately and placed in `car-segmentation-ms/model/`: `sam_vit_b_01ec64.pth`, `yolov11seg.pt`, `yolov10n.pt`.

---

## Planned Features

- MVP: Change car color (mask creation + color-modified generation)
- Spoilers, rims, body kits, lighting modifications
- Background / environment changes (weather, location, lighting style)
- User-drawn masks for custom region selection

---

## Development Notes

- Add new microservices as sibling directories (`car-<name>-ms/`) with their own `environment.yml` and Conda env.
- `car-backend-ms` env must stay ML-free — heavy deps belong only in `sam-microservice`.
- Keep model weights out of git — use `car-segmentation-ms/model/` which is gitignored.
- `environment.yml` in each service directory is the source of truth for its dependencies.
- Do not use plain `pip install` outside of the Conda envs.
