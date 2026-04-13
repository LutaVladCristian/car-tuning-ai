# Dev GCP Infrastructure

Terraform scaffold for the first hosted `dev` environment.

Chosen defaults:

- Region: `europe-central2` (Warsaw)
- Zone: `europe-central2-b`
- Frontend: Cloud Run
- Backend: Cloud Run
- Segmentation: private Compute Engine GPU VM
- Database: Cloud SQL PostgreSQL
- Image/model storage: Cloud Storage
- CI/CD auth: GitHub Actions Workload Identity Federation

Cloud Functions was considered for `car-segmentation-ms`, but it is not the serving target for this repo because the service needs GPU-oriented model serving, large ML dependencies, model weights, and predictable long-lived process startup. Cloud Run functions are a poor fit for this SAM/YOLO inference service; keep segmentation on a GPU VM for dev unless the model is later split into a lighter asynchronous pipeline.

## Bootstrap

1. Create a GCP project manually and note its project ID.
2. Create or select a Terraform state bucket. Keep it outside this config to avoid bootstrapping Terraform with itself.
3. Create `terraform.tfvars` from `terraform.tfvars.example`.
4. Run:

```bash
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```

## GitHub Secrets / Variables

Set these in the repo or `dev` GitHub Environment after the first apply:

- `GCP_PROJECT_ID`
- `GCP_WORKLOAD_IDENTITY_PROVIDER`
- `GCP_DEPLOYER_SERVICE_ACCOUNT`
- `GCP_REGION`
- `DEV_BACKEND_URL`

Use repository variables, not secrets, for non-sensitive URLs and regions.
