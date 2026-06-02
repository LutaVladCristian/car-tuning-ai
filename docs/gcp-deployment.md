# GCP Deployment Guide

## Architecture

| Service | Target | Notes |
|---|---|---|
| `car-backend-ms` | Cloud Run | Auth gateway, database migrations, Firebase Storage writes |
<<<<<<< HEAD
| `car-segmentation-ms` | Cloud Run GPU | IAM-protected; downloads model weights from GCS at startup |
| `car-frontend` | Firebase Hosting | SPA at `https://slick-tunes.web.app` |
| PostgreSQL | Cloud SQL | Persistent metadata |
| Photos | Firebase Storage | Original, prepared, mask, and result PNG files |
| Model weights | GCS bucket `car-tuning-ai-vision-models` | SAM ViT-H and YOLOv10n weights |
=======
| `car-segmentation-ms` | Cloud Run GPU | IAM-protected; model weights baked into its image |
| `car-frontend` | Firebase Hosting | SPA at `https://slick-tunes.web.app` |
| PostgreSQL | Cloud SQL | Persistent metadata |
| Photos | Firebase Storage | Original, prepared, mask, and result PNG files |
>>>>>>> 81e17ab068b83971db188396d0af1845e2a8bef3
| Secrets | Secret Manager | `OPENAI_API_KEY` and `DATABASE_URL` |

## Firebase Storage

The backend writes user photo artifacts under:

```text
users/{firebase_uid}/photos/{uuid}/{role}.png
```

Roles are `original`, `prepared`, `raw-mask`, `mask`, and `result`. Firebase rules deny client writes and allow authenticated users to read only their own files.

<<<<<<< HEAD
## Model Weight Bucket

Model weights remain gitignored. Upload them once to the deployment bucket:

```bash
gcloud storage buckets create gs://car-tuning-ai-vision-models \
  --location=europe-west1 \
  --uniform-bucket-level-access

gcloud storage cp car-segmentation-ms/model/sam_vit_h_4b8939.pth gs://car-tuning-ai-vision-models/
gcloud storage cp car-segmentation-ms/model/yolov10n.pt gs://car-tuning-ai-vision-models/

gcloud storage buckets add-iam-policy-binding gs://car-tuning-ai-vision-models \
  --member="serviceAccount:segmentation-ms-sa@car-tuning-ai-494319.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"
```

`download_models.py` downloads missing weights into `/app/model/` before importing the ML pipeline. For local development, place the same files in `car-segmentation-ms/model/`; local files skip the download.

## Segmentation Image

The image contains code and dependencies only, so GitHub Actions can build and push it at merge time:
=======
## Segmentation Image

Model weights are gitignored and baked into the image. Place these files locally before building:

```text
car-segmentation-ms/model/sam_vit_h_4b8939.pth
car-segmentation-ms/model/yolov10n.pt
```

Build and push from a machine that has the weights:
>>>>>>> 81e17ab068b83971db188396d0af1845e2a8bef3

```bash
gcloud auth configure-docker
docker build -t gcr.io/car-tuning-ai-494319/car-segmentation-ms car-segmentation-ms/
docker push gcr.io/car-tuning-ai-494319/car-segmentation-ms
```

<<<<<<< HEAD
=======
The GitHub workflow does not build the segmentation image because the weight files are intentionally absent from the repository. Push the baked image before merging a segmentation change; the workflow deploys that pre-built tag with the startup probe.

>>>>>>> 81e17ab068b83971db188396d0af1845e2a8bef3
## Deploy Segmentation

```bash
gcloud run deploy car-segmentation-ms \
  --image gcr.io/car-tuning-ai-494319/car-segmentation-ms \
  --region europe-west1 \
  --service-account segmentation-ms-sa@car-tuning-ai-494319.iam.gserviceaccount.com \
  --update-secrets OPENAI_API_KEY=car-backend-openai-key:latest \
<<<<<<< HEAD
  --set-env-vars MODEL_BUCKET=car-tuning-ai-vision-models \
=======
>>>>>>> 81e17ab068b83971db188396d0af1845e2a8bef3
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
  --timeout 600 \
  --startup-probe httpGet.path=/health,httpGet.port=8080,periodSeconds=5,timeoutSeconds=5,failureThreshold=24
```

<<<<<<< HEAD
The `5 x 24 = 120` second startup-probe window prevents traffic from reaching a revision until the weights download and SAM/YOLO initialization complete.
=======
The `5 × 24 = 120` second startup-probe window prevents traffic from reaching a revision until SAM and YOLO initialization completes. Baking the weights removes runtime download latency but does not remove GPU initialization time.
>>>>>>> 81e17ab068b83971db188396d0af1845e2a8bef3

## Deploy Backend

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

<<<<<<< HEAD
The backend service account needs `roles/run.invoker` on `car-segmentation-ms` and Cloud SQL access. The segmentation service account needs Secret Manager access for `OPENAI_API_KEY` and `roles/storage.objectViewer` on the model bucket.

## Frontend And Workflow

`.github/workflows/deploy.yml` builds and deploys the backend, segmentation service, and frontend after a pull request into `main` is merged. Frontend hosting deploys use:
=======
The backend service account needs `roles/run.invoker` on `car-segmentation-ms` and Cloud SQL access. The segmentation service account needs Secret Manager access for `OPENAI_API_KEY`.

## Frontend And Workflow

`.github/workflows/deploy.yml` builds the backend and frontend, deploys them, and deploys the pre-built segmentation image after a pull request into `main` is merged. Frontend hosting deploys use:
>>>>>>> 81e17ab068b83971db188396d0af1845e2a8bef3

```bash
cd car-frontend
npm run build
firebase deploy --only hosting --project slick-tunes
```

## Local Run

```bash
# Terminal 1
cd car-segmentation-ms
conda run -n sam-microservice uvicorn server:app --host 0.0.0.0 --port 8000

# Terminal 2
cd car-backend-ms
conda run -n car-backend-ms alembic upgrade head
conda run -n car-backend-ms uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Terminal 3
cd car-frontend
npm run dev
```
