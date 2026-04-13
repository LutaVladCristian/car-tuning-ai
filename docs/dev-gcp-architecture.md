# Dev GCP Architecture

This document records the selected `dev` hosting path for Car Tuning AI.

## Decisions

| Area | Decision |
|---|---|
| Region | `europe-central2` (Warsaw) |
| Zone | `europe-central2-b` |
| Frontend hosting | Cloud Run |
| Backend hosting | Cloud Run |
| Segmentation hosting | Compute Engine GPU VM, private to backend |
| Auth | Google Identity Platform / Firebase Auth, email/password + Google login |
| Database | Cloud SQL PostgreSQL |
| Image storage | Cloud Storage |
| Model storage | Cloud Storage |
| Infra | Terraform |
| CI/CD | GitHub Actions with Workload Identity Federation |

Warsaw was selected because it is close to Bucharest and the Google Cloud regions/zones table marks `europe-central2-b` and `europe-central2-c` as GPU-capable zones. GPU quota and the exact accelerator type still need to be confirmed in the target project before applying Terraform.

## Runtime Flow

```text
Browser
  -> Cloud Run frontend
  -> Cloud Run backend
  -> private segmentation GPU VM
  -> OpenAI Images API

Cloud Run backend
  -> Cloud SQL PostgreSQL
  -> Cloud Storage photos bucket
```

Only the frontend and backend are public. The segmentation VM should not be publicly invoked by users; the backend is the only caller.

## Cloud Functions Assessment

Cloud Functions / Cloud Run functions are not the right serving target for `car-segmentation-ms` right now.

Reasons:

- The service loads large ML dependencies and model weights.
- The current pipeline expects SAM + YOLO model serving, which is GPU-oriented.
- Function cold starts would be painful for this workload.
- Function-style deployment is better for short request handlers or event jobs, not long-lived in-memory model serving.

If the product later changes to an asynchronous pipeline, a function could enqueue work or handle lightweight orchestration, but the model runner should remain on a GPU-capable service.

## Auth Migration

Replace custom password auth with Firebase/Identity Platform:

1. Frontend signs users in with Firebase Auth.
2. Supported providers for dev: email/password and Google login.
3. Frontend sends Firebase ID token as `Authorization: Bearer <id_token>`.
4. Backend verifies the token with Firebase Admin SDK.
5. Backend user/profile rows are keyed by Firebase `uid`.
6. Remove custom password hashing/JWT issuance once migration is complete.

Suggested DB direction:

- `users.id`: internal primary key.
- `users.firebase_uid`: unique, non-null once migrated.
- `users.email`: from Firebase token/profile.
- `users.display_name`: optional.
- Remove or deprecate `hashed_password` after data migration.

## Image Storage Migration

Move original and result image bytes out of PostgreSQL and into Cloud Storage.

Suggested `photos` shape:

- `original_object_key`
- `result_object_key`
- `mime_type`
- `byte_size`
- `operation_type`
- `operation_params`
- `created_at`

The backend should stream uploads/results to GCS and store only metadata in Cloud SQL. This keeps the DB smaller and makes image retention easier to manage.

## Migration Policy

Every DB model change must include an Alembic migration.

The PR gate should run:

- `alembic upgrade head`
- `alembic check`
- Backend unit tests with `pytest`
- Frontend unit tests with `npm test`
- Segmentation unit tests with `pytest`
- `alembic downgrade base`
- `alembic upgrade head`

Use a real Postgres service in CI so JSON/enums/timestamps behave like production. Segmentation unit tests use SAM/YOLO test doubles so PR checks do not require GPU or model weights.

## Dev Deploy Policy

On push to `main`:

1. Authenticate GitHub Actions to GCP via Workload Identity Federation.
2. Build frontend, backend, and segmentation images.
3. Push images to Artifact Registry.
4. Run Alembic migrations as a Cloud Run Job.
5. Deploy frontend and backend to Cloud Run.
6. Update the segmentation VM container image.

Production is intentionally out of scope until the dev layer is stable.

## GitHub Actions Workflows

The workflow directory intentionally contains only:

- `.github/workflows/pr-checks.yml`: PR validation for frontend lint/test/build, backend lint/test/migrations, segmentation lint/test, Terraform validation, and Docker build smoke checks.
- `.github/workflows/deploy-dev.yml`: automatic dev deployment after merge to `main`.

Older service-specific workflows were removed to avoid duplicate status checks and duplicate image builds.
