# GCP Deployment Guide

## Architecture

| Service | Target | Notes |
|---|---|---|
| `car-backend-ms` | Cloud Run (port 8080) | Runs `alembic upgrade head` on every cold start |
| `car-segmentation-ms` | Cloud Run (port 8080) | Downloads models from GCS at startup; IAM-protected (`--no-allow-unauthenticated`) |
| `car-frontend` | Firebase Hosting | SPA with `/index.html` rewrite rule; project `slick-tunes` -> `https://slick-tunes.web.app` |
| PostgreSQL | Cloud SQL | `car-tuning-db` in `europe-west1`; connected via Unix socket sidecar |
| Photos | Firebase Storage | `users/{uid}/photos/{uuid}/{role}.png` for `original`, `result`, and `mask`; bucket `slick-tunes.firebasestorage.app` |
| Model weights | GCS bucket `car-tuning-ai-vision-models` | SAM ViT-H (~2.56 GB) + YOLOv10n COCO detector (~6 MB) |
| Secrets | Secret Manager | `OPENAI_API_KEY` -> `car-backend-openai-key`, `DATABASE_URL` -> `car-backend-db-url` |

---

## 1. GCS Bucket - Model Weights

### Create bucket

```bash
gcloud storage buckets create gs://car-tuning-ai-vision-models \
  --location=europe-west1 \
  --uniform-bucket-level-access
```

### Upload weights

```bash
cd car-segmentation-ms/model/
gcloud storage cp sam_vit_h_4b8939.pth gs://car-tuning-ai-vision-models/
gcloud storage cp yolov10n.pt           gs://car-tuning-ai-vision-models/
```

### IAM - segmentation service account

```bash
gcloud iam service-accounts create segmentation-ms-sa \
  --display-name="car-segmentation-ms Cloud Run SA"

gcloud storage buckets add-iam-policy-binding gs://car-tuning-ai-vision-models \
  --member="serviceAccount:segmentation-ms-sa@car-tuning-ai-494319.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"
```

How it works: `download_models.py` is called inside `_load_models()` in `server.py` in a background thread. It reads `MODEL_BUCKET` and downloads missing model files into `car-segmentation-ms/model/`.

---

## 2. Firebase Storage - Photo Images

### Enable in Firebase console

Firebase console -> Storage -> Get started -> bucket name is `slick-tunes.firebasestorage.app`.

### Security rules

```text
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /users/{userId}/photos/{allPaths=**} {
      allow read: if request.auth != null && request.auth.uid == userId;
      allow write: if false;
    }
  }
}
```

### Local dev with emulator

```bash
cd car-frontend
firebase emulators:start --only storage
# Emulator UI: http://localhost:4000 | Storage: localhost:9199
```

Add to root `.env`:

```dotenv
FIREBASE_STORAGE_EMULATOR_HOST=127.0.0.1:9199
```

Photo storage path: `users/{firebase_uid}/photos/{uuid}/{role}.png`, where `role` is `original`, `result`, or `mask`. The backend writes these objects with service-account credentials; client-side Firebase Storage writes are denied by rules.

---

## 3. Secret Manager

### Create secrets

```bash
echo -n "sk-..." | gcloud secrets create car-backend-openai-key --data-file=-
echo -n "postgresql+psycopg2://car-user:PASSWORD@/car_tuning?host=/cloudsql/car-tuning-ai-494319:europe-west1:car-tuning-db" \
  | gcloud secrets create car-backend-db-url --data-file=-
```

`DATABASE_URL` for Cloud Run must use the Unix socket path. Cloud Run injects the Cloud SQL Auth Proxy sidecar at `/cloudsql/<project>:<region>:<instance>`.

### Grant access

```bash
gcloud iam service-accounts create backend-ms-sa \
  --display-name="car-backend-ms Cloud Run SA"

# Secret Manager access
gcloud secrets add-iam-policy-binding car-backend-db-url \
  --member="serviceAccount:backend-ms-sa@car-tuning-ai-494319.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding car-backend-openai-key \
  --member="serviceAccount:segmentation-ms-sa@car-tuning-ai-494319.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Cloud SQL access for backend
gcloud projects add-iam-policy-binding car-tuning-ai-494319 \
  --member="serviceAccount:backend-ms-sa@car-tuning-ai-494319.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"
```

Secrets are injected as env vars in `gcloud run deploy` via `--update-secrets`.

---

## 4. Cloud Run - Service-to-Service Auth

`car-segmentation-ms` is deployed with `--no-allow-unauthenticated` and `--ingress all`.

Cloud Run services calling each other via `*.run.app` URLs go through Google's public load balancer, which counts as external traffic. `--ingress internal` blocks that path. `--ingress all` plus IAM keeps the service private to authorized callers.

`car-backend-ms` gets a GCP-signed identity token from the metadata server on each call to the segmentation service:

```python
# car-backend-ms/app/services/proxy_service.py
token = await _identity_token(audience=settings.SEGMENTATION_MS_URL)
# token is None outside GCP, so local dev sends no Authorization header
```

Production backend deployments set `REQUIRE_SEGMENTATION_IAM=true`, so Cloud Run calls fail closed if the identity token cannot be fetched.

### One-time IAM grant

```bash
gcloud run services add-iam-policy-binding car-segmentation-ms \
  --region europe-west1 \
  --member="serviceAccount:backend-ms-sa@car-tuning-ai-494319.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

---

## 5. Cloud Run Deployment

### IAM for GitHub Actions deploy service account

```bash
# Artifact Registry (GCR is backed by Artifact Registry)
gcloud projects add-iam-policy-binding car-tuning-ai-494319 \
  --member="serviceAccount:github-deploy-sa@car-tuning-ai-494319.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

# Cloud Run deploy
gcloud projects add-iam-policy-binding car-tuning-ai-494319 \
  --member="serviceAccount:github-deploy-sa@car-tuning-ai-494319.iam.gserviceaccount.com" \
  --role="roles/run.developer"

# Act as backend and segmentation service accounts
gcloud iam service-accounts add-iam-policy-binding \
  backend-ms-sa@car-tuning-ai-494319.iam.gserviceaccount.com \
  --member="serviceAccount:github-deploy-sa@car-tuning-ai-494319.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud iam service-accounts add-iam-policy-binding \
  segmentation-ms-sa@car-tuning-ai-494319.iam.gserviceaccount.com \
  --member="serviceAccount:github-deploy-sa@car-tuning-ai-494319.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

### Build and push manually

```bash
gcloud auth configure-docker

docker build -t gcr.io/car-tuning-ai-494319/car-backend-ms car-backend-ms/
docker push gcr.io/car-tuning-ai-494319/car-backend-ms

docker build -t gcr.io/car-tuning-ai-494319/car-segmentation-ms car-segmentation-ms/
docker push gcr.io/car-tuning-ai-494319/car-segmentation-ms
```

### Deploy backend manually

```bash
gcloud run deploy car-backend-ms \
  --image gcr.io/car-tuning-ai-494319/car-backend-ms \
  --region europe-west1 \
  --service-account backend-ms-sa@car-tuning-ai-494319.iam.gserviceaccount.com \
  --add-cloudsql-instances car-tuning-ai-494319:europe-west1:car-tuning-db \
  --update-secrets DATABASE_URL=car-backend-db-url:latest \
  --set-env-vars "FIREBASE_PROJECT_ID=slick-tunes,FIREBASE_STORAGE_BUCKET=slick-tunes.firebasestorage.app,SEGMENTATION_MS_URL=https://car-segmentation-ms-130079365217.europe-west1.run.app,CORS_ORIGINS=[\"https://slick-tunes.web.app\"],REQUIRE_SEGMENTATION_IAM=true" \
  --allow-unauthenticated
```

### Deploy segmentation-ms manually

```bash
gcloud run deploy car-segmentation-ms \
  --image gcr.io/car-tuning-ai-494319/car-segmentation-ms \
  --region europe-west1 \
  --service-account segmentation-ms-sa@car-tuning-ai-494319.iam.gserviceaccount.com \
  --update-secrets OPENAI_API_KEY=car-backend-openai-key:latest \
  --set-env-vars MODEL_BUCKET=car-tuning-ai-vision-models \
  --no-allow-unauthenticated \
  --ingress all \
  --cpu-boost \
  --gpu 1 \
  --gpu-type nvidia-l4 \
  --cpu 8 \
  --memory 16Gi \
  --concurrency 1 \
  --max-instances 1 \
  --no-gpu-zonal-redundancy \
  --no-cpu-throttling \
  --timeout 600
```

Cold start sequence: port opens immediately, models download from GCS in the background, SAM ViT-H loads into GPU memory, and the service returns HTTP 503 until `_models_ready` is set.

---

## 6. Firebase Hosting

Deployments are automated by `.github/workflows/deploy.yml` when a PR into `main` is merged. The frontend job runs `npm ci`, `npm run build`, then `npx firebase-tools deploy --only hosting --project slick-tunes`.

For manual deploy:

```bash
cd car-frontend
VITE_API_BASE_URL=https://car-backend-ms-130079365217.europe-west1.run.app npm run build
firebase deploy --only hosting --project slick-tunes
```

`.firebaserc` is committed with project ID `slick-tunes`. Live URL: `https://slick-tunes.web.app`. The frontend browser tab title comes from `car-frontend/index.html` and is `slick-tunes`.

Firebase Hosting security headers are configured in `car-frontend/firebase.json`; the Nginx headers only apply to Docker/Nginx deployments.

---

## 7. Environment Variables Reference

| Variable | Where used | Secret Manager? |
|---|---|---|
| `DATABASE_URL` | backend-ms | Yes, `car-backend-db-url` |
| `FIREBASE_PROJECT_ID` | backend-ms | No, value: `slick-tunes` |
| `FIREBASE_STORAGE_BUCKET` | backend-ms | No, value: `slick-tunes.firebasestorage.app` |
| `SEGMENTATION_MS_URL` | backend-ms | No, value: `https://car-segmentation-ms-130079365217.europe-west1.run.app` |
| `CORS_ORIGINS` | backend-ms | No, value: `["https://slick-tunes.web.app"]` |
| `REQUIRE_SEGMENTATION_IAM` | backend-ms | No, production value: `true` |
| `OPENAI_API_KEY` | segmentation-ms | Yes, `car-backend-openai-key` |
| `MODEL_BUCKET` | segmentation-ms | No, value: `car-tuning-ai-vision-models` |
| `VITE_API_BASE_URL` | frontend build | GitHub secret |
| `VITE_FIREBASE_*` | frontend build | GitHub secrets |

---

## 8. GitHub Secrets Required

| Secret | Used by |
|---|---|
| `GCP_SA_KEY` | Deploy jobs; JSON key for `github-deploy-sa` |
| `FIREBASE_SERVICE_ACCOUNT_SLICK_TUNES` | Frontend deploy; Firebase service account key JSON |
| `VITE_API_BASE_URL` | Frontend build |
| `VITE_FIREBASE_API_KEY` | Frontend build |
| `VITE_FIREBASE_AUTH_DOMAIN` | Frontend build |
| `VITE_FIREBASE_PROJECT_ID` | Frontend build |
| `VITE_FIREBASE_STORAGE_BUCKET` | Frontend build |
| `VITE_FIREBASE_MESSAGING_SENDER_ID` | Frontend build |
| `VITE_FIREBASE_APP_ID` | Frontend build |

---

## 9. Local Testing

```bash
# Start Firebase Storage emulator
cd car-frontend && firebase emulators:start --only storage

# Terminal 1 - segmentation-ms
cd car-segmentation-ms
conda run -n sam-microservice uvicorn server:app --host 0.0.0.0 --port 8000

# Terminal 2 - backend
cd car-backend-ms
conda run -n car-backend-ms bash -c "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8001 --reload"

# Terminal 3 - frontend
cd car-frontend && npm run dev

# Run tests
conda run -n car-backend-ms python -m pytest tests/ --tb=short -q
conda run -n sam-microservice python -m pytest tests/ --tb=short -q
cd car-frontend && npm test
```

Local identity token behavior: `proxy_service.py` fetches an identity token from the GCP metadata server. Outside GCP the fetch returns `None` and no `Authorization` header is sent, so local segmentation without IAM keeps working while `REQUIRE_SEGMENTATION_IAM=false`.
