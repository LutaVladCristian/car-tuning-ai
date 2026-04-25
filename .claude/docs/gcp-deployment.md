# GCP Deployment Guide

## Architecture

| Service | Target | Notes |
|---|---|---|
| `car-backend-ms` | Cloud Run (port 8001) | Runs `alembic upgrade head` on every cold start |
| `car-segmentation-ms` | Cloud Run (port 8000) | Downloads models from GCS at startup; internal-only |
| `car-frontend` | Firebase Hosting | SPA with `/index.html` rewrite rule |
| PostgreSQL | Cloud SQL | Metadata only — no image blobs |
| Photos (images) | Firebase Storage | `users/{uid}/photos/{uuid}/{role}.png` |
| Model weights | GCS bucket `car-tuning-ai-models` | SAM (~2.56 GB) + YOLO (~18 MB) |
| Secrets | Secret Manager | `OPENAI_API_KEY`, `DATABASE_URL` |

---

## 1. GCP Bucket — Model Weights

### Create bucket
```bash
gcloud storage buckets create gs://car-tuning-ai-vision-models \
  --location=us-central1 \
  --uniform-bucket-level-access
```

### Upload weights
```bash
cd car-segmentation-ms/model/
gcloud storage cp sam_vit_h_4b8939.pth gs://car-tuning-ai-vision-models/
gcloud storage cp yolov11n.pt           gs://car-tuning-ai-vision-models/ 
```

### IAM — segmentation service account
```bash
gcloud iam service-accounts create segmentation-ms-sa \
  --display-name="car-segmentation-ms Cloud Run SA"

gcloud storage buckets add-iam-policy-binding gs://car-tuning-ai-vision-models \
  --member="serviceAccount:segmentation-ms-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"
```

How it works: `car-segmentation-ms/download_models.py` runs before uvicorn at each cold start. It reads `MODEL_BUCKET` env var; if unset, it skips (local dev with `./model/` files).

---

## 2. Firebase Storage — Photo Images

### Enable in Firebase console
Firebase console → Storage → Get started → note bucket name (`PROJECT_ID.firebasestorage.app`).

### Security rules
```
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /users/{userId}/photos/{allPaths=**} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

### Local dev with emulator
```bash
cd car-frontend
firebase emulators:start --only storage
# Emulator UI: http://localhost:4000  |  Storage: localhost:9199
```
Add to root `.env`:
```dotenv
FIREBASE_STORAGE_EMULATOR_HOST=127.0.0.1:9199
```

Photo storage path: `users/{firebase_uid}/photos/{uuid}/{role}.png` where role is `original` or `result`.

---

## 3. Secret Manager

### Create secrets
```bash
echo -n "sk-..." | gcloud secrets create car-backend-openai-key --data-file=-
echo -n "postgresql://..." | gcloud secrets create car-backend-db-url --data-file=-
```

### Grant access
```bash
gcloud iam service-accounts create backend-ms-sa \
  --display-name="car-backend-ms Cloud Run SA"

gcloud secrets add-iam-policy-binding car-backend-db-url \
  --member="serviceAccount:backend-ms-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding car-backend-openai-key \
  --member="serviceAccount:segmentation-ms-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

Secrets are injected as env vars in `gcloud run deploy` via `--update-secrets`.

---

## 4. Cloud Run Deployment

### Build and push
```bash
gcloud auth configure-docker

docker build -t gcr.io/PROJECT_ID/car-backend-ms car-backend-ms/
docker push gcr.io/PROJECT_ID/car-backend-ms

docker build -t gcr.io/PROJECT_ID/car-segmentation-ms car-segmentation-ms/
docker push gcr.io/PROJECT_ID/car-segmentation-ms
```

### Deploy backend
```bash
gcloud run deploy car-backend-ms \
  --image gcr.io/PROJECT_ID/car-backend-ms \
  --region us-central1 \
  --service-account backend-ms-sa@PROJECT_ID.iam.gserviceaccount.com \
  --update-secrets DATABASE_URL=car-backend-db-url:latest \
  --set-env-vars "FIREBASE_PROJECT_ID=PROJECT_ID,FIREBASE_STORAGE_BUCKET=PROJECT_ID.firebasestorage.app,SEGMENTATION_MS_URL=https://car-segmentation-ms-HASH-uc.a.run.app,CORS_ORIGINS=[\"https://PROJECT_ID.web.app\"]" \
  --allow-unauthenticated
```

### Deploy segmentation-ms (internal-only)
```bash
gcloud run deploy car-segmentation-ms \
  --image gcr.io/PROJECT_ID/car-segmentation-ms \
  --region us-central1 \
  --service-account segmentation-ms-sa@PROJECT_ID.iam.gserviceaccount.com \
  --update-secrets OPENAI_API_KEY=car-backend-openai-key:latest \
  --set-env-vars MODEL_BUCKET=car-tuning-ai-models \
  --no-allow-unauthenticated \
  --ingress internal
```

---

## 5. Firebase Hosting (Frontend)

```bash
cd car-frontend

# Build with production API URL baked in
VITE_API_BASE_URL=https://car-backend-ms-HASH-uc.a.run.app npm run build

# Deploy
firebase deploy --only hosting
```

`.firebaserc` is already committed with the project ID. `firebase.json` already has the SPA rewrite rule.

---

## 6. Environment Variables Reference

| Variable | Where used | Secret Manager? |
|---|---|---|
| `DATABASE_URL` | backend-ms | Yes — `car-backend-db-url` |
| `FIREBASE_PROJECT_ID` | backend-ms | No |
| `FIREBASE_STORAGE_BUCKET` | backend-ms | No |
| `SEGMENTATION_MS_URL` | backend-ms | No |
| `CORS_ORIGINS` | backend-ms | No |
| `OPENAI_API_KEY` | segmentation-ms | Yes — `car-backend-openai-key` |
| `MODEL_BUCKET` | segmentation-ms | No |
| `VITE_API_BASE_URL` | frontend (build time) | No |
| `VITE_FIREBASE_*` | frontend (build time) | No |

---

## 7. Local Testing

```bash
# Start Firebase Storage emulator
cd car-frontend && firebase emulators:start --only storage

# Terminal 1 — segmentation-ms (no MODEL_BUCKET → uses local ./model/)
conda run -n sam-microservice uvicorn server:app --host 0.0.0.0 --port 8000

# Terminal 2 — backend (migrates DB then starts)
conda run -n car-backend-ms bash -c "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8001 --reload"

# Terminal 3 — frontend
cd car-frontend && npm run dev

# Run tests
conda run -n car-backend-ms python -m pytest tests/ --tb=short -q
conda run -n sam-microservice python -m pytest tests/ --tb=short -q
cd car-frontend && npm test
```
