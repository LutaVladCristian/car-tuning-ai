# car-backend-ms

FastAPI gateway service: Firebase auth, upload validation, photo metadata persistence, Firebase Storage image storage, and proxying to `car-segmentation-ms`.

**Conda env:** `car-backend-ms` (Python 3.12, no ML deps)
**Port:** 8001 locally; Cloud Run uses the injected `PORT` value.
**Config:** `pydantic-settings` reads `../.env` from the repo root.

## Commands

See [README.md](../../README.md) for setup, local run commands, and tests.

## Structure

```
car-backend-ms/
|-- main.py                    # FastAPI app, CORS, router registration, GET /health
|-- config.py                  # pydantic-settings reads ../.env
|-- dependencies.py            # Firebase token verification + DB session dependencies
|-- alembic/
|   `-- versions/              # DB migrations
`-- app/
    |-- core/
    |   `-- security.py        # Firebase Admin app + ID token verification
    |-- db/
    |   |-- session.py         # SQLAlchemy engine + SessionLocal
    |   |-- base.py            # declarative Base
    |   `-- models/
    |       |-- user.py        # User ORM
    |       `-- photo.py       # Photo ORM + OperationType enum
    |-- routers/
    |   |-- auth.py            # POST /auth/firebase
    |   |-- photos.py          # GET /photos, GET /photos/{id}, GET /photos/{id}/original
    |   `-- segmentation.py    # Preview, approve, and cancel edit flow
    |-- schemas/               # Pydantic response models
    `-- services/
        |-- proxy_service.py   # httpx forwarding to car-segmentation-ms
        `-- storage_service.py # Firebase Storage upload/download helpers
```

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | None | Health check |
| POST | `/auth/firebase` | None | Exchange Firebase ID token for a synced backend user record |
| GET | `/photos` | Bearer | List current user's photo metadata with pagination (`skip`, `limit`) |
| GET | `/photos/{photo_id}` | Bearer | Stream the result PNG if present, otherwise the original image |
| GET | `/photos/{photo_id}/original` | Bearer | Stream the original uploaded PNG for comparison views |
| POST | `/edit-photo/preview` | Bearer | Run YOLO + SAM and persist a hidden mask preview |
| POST | `/edit-photo/{id}/generate` | Bearer | Generate an approved preview with OpenAI |
| DELETE | `/edit-photo/{id}/preview` | Bearer | Delete an unapproved preview |
| GET | `/photos/{id}/mask/raw` | Bearer | Stream the binary SAM car mask |
| GET | `/photos/{id}/mask/edit` | Bearer | Stream the effective OpenAI RGBA mask |

## Auth Flow

1. Browser signs in with Firebase Google Sign-In and receives an ID token.
2. `POST /auth/firebase` receives `{id_token}`, verifies it with `firebase-admin`, upserts a `User` row keyed by `firebase_uid`, and returns the backend user record.
3. Protected endpoints read `Authorization: Bearer <token>`, verify the token, and resolve the current `User` from the database. Missing or invalid tokens return HTTP 401.

## Upload and Proxy Flow

`POST /edit-photo/preview` validates the upload, calls segmentation, and stores the original, prepared input, raw mask, and effective OpenAI mask. Preview records stay hidden from history.

`POST /edit-photo/{id}/generate` claims an approved preview, calls OpenAI through the segmentation service, saves the result, and marks the record completed. Failed generation restores the preview state for retry. Completed records are idempotent and return their stored result.

Outside GCP, `_identity_token()` returns `None`, so local backend-to-segmentation calls omit the `Authorization` header unless `REQUIRE_SEGMENTATION_IAM=true`. In Cloud Run, the backend gets a metadata-server identity token for the segmentation service audience and production deploys fail closed if that token cannot be fetched.

## Database Schema

**`users` table**

| Column | Type | Constraints |
|---|---|---|
| `id` | integer | PK, auto-increment |
| `firebase_uid` | varchar(128) | unique, not null, indexed |
| `email` | varchar(255) | unique, not null |
| `display_name` | varchar(255) | nullable |
| `created_at` | timestamp | default now() |

**`photos` table**

| Column | Type | Constraints |
|---|---|---|
| `id` | integer | PK, auto-increment |
| `user_id` | integer | FK to `users.id`, not null |
| `original_filename` | varchar(255) | not null |
| `original_image_path` | string | Firebase Storage path, not null |
| `prepared_image_path` | string | Prepared inference image path, nullable |
| `result_image_path` | string | Firebase Storage path, nullable |
| `raw_mask_image_path` | string | Binary SAM car mask path, nullable |
| `mask_image_path` | string | Firebase Storage path, nullable |
| `status` | enum | `preview`, `generating`, or `completed` |
| `operation_type` | enum | currently `edit_photo` |
| `operation_params` | JSON | `prompt`, `edit_car`, `size` |
| `created_at` | timestamp | default now() |

Current migration files include the initial schema, Firebase auth update, blob-to-storage-path migration, mask storage, and preview state. Keep new migrations in `car-backend-ms/alembic/versions/`.

## Storage

Image bytes are stored in Firebase Storage, not PostgreSQL. Paths follow:

```
users/{firebase_uid}/photos/{uuid}/{role}.png
```

`role` is `original`, `prepared`, `raw-mask`, `mask`, or `result`. Unsupported role names are rejected before upload, and blob metadata includes the Firebase UID and role.

## Proxy Timeout

- `/edit-photo/preview` and `/edit-photo/{id}/generate`: 180 seconds, because segmentation and OpenAI generation can each be slow.
