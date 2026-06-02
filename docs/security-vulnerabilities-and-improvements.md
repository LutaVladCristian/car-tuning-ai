# Security Vulnerabilities And Improvements Report

Date: 2026-04-26

## Executive Summary

This report is a repo-grounded security and hardening review of `car-backend-ms`, `car-segmentation-ms`, `car-frontend`, Dockerfiles, CI/CD workflows, deployment docs, and dependency manifests.

No frontend npm vulnerabilities were reported by a second local `npm audit --json` run. Python dependency audit tooling and local secret scanning were still not available in this workstation environment, so those results should be treated as incomplete until CI or a machine with `pip-audit` and `gitleaks` installed reruns them.

Remediation has started. Several code-level and deployment-level controls are now implemented; project-level items such as GCP Workload Identity Federation, image digest pinning, and formal data-retention policy still require deployment or product decisions.

The highest-value remaining improvements are:

1. Replace long-lived GCP deploy keys with GitHub OIDC Workload Identity Federation.
2. Replace large base64 JSON image payloads with streaming, multipart, or storage-backed transfer.
3. Add persistent, cross-instance quota controls and cost telemetry for OpenAI/GPU requests.
4. Define retention policy for originals, generated results, masks, and prompts.
5. Add Docker image digest pinning, SBOM generation, and image vulnerability scanning.

## Methodology And Commands Run

Static review focused on security-sensitive paths:

```powershell
rg -n "TODO|FIXME|HACK|password|secret|token|api_key|OPENAI_API_KEY|allow-unauthenticated|CORS|verify|upload|Storage|HTTPException|except Exception|eval\(|subprocess|shell=True|pickle|yaml.load|debug|localhost|0.0.0.0" car-backend-ms car-segmentation-ms car-frontend .github .env.example -S --glob '!**/node_modules/**' --glob '!**/dist/**' --glob '!**/.pytest_cache/**' --glob '!**/output/**'
Get-Content car-backend-ms\Dockerfile
Get-Content car-segmentation-ms\Dockerfile
Get-Content car-frontend\Dockerfile
Get-Content car-frontend\nginx.conf
Get-Content .github\workflows\pr-checks.yml
Get-Content .github\workflows\deploy.yml
Get-Content car-backend-ms\app\routers\segmentation.py
Get-Content car-backend-ms\app\services\proxy_service.py
Get-Content car-backend-ms\app\services\storage_service.py
Get-Content car-backend-ms\app\core\security.py
Get-Content car-segmentation-ms\server.py
```

Dependency and secret audit attempts:

```powershell
npm audit --json
C:\Users\vlad_cristian.luta\AppData\Local\anaconda3\envs\car-backend-ms\python.exe -m pip_audit -r requirements.txt
C:\Users\vlad_cristian.luta\AppData\Local\anaconda3\envs\sam-microservice\python.exe -m pip_audit -r requirements.txt
gitleaks detect --source . --redact --verbose
```

Second-pass verification and image-preservation checks:

```powershell
rg -n "TODO|FIXME|HACK|password|secret|token|api_key|OPENAI_API_KEY|allow-unauthenticated|CORS|verify|upload|Storage|HTTPException|except Exception|eval\(|subprocess|shell=True|pickle|yaml.load|debug|localhost|0\.0\.0\.0" car-backend-ms car-segmentation-ms car-frontend .github .env.example -S --glob '!**/node_modules/**' --glob '!**/dist/**' --glob '!**/.pytest_cache/**' --glob '!**/output/**'
npm audit --json
C:\Users\vlad_cristian.luta\AppData\Local\anaconda3\envs\sam-microservice\python.exe -m pytest --tb=short -q
C:\Users\vlad_cristian.luta\AppData\Local\anaconda3\envs\car-backend-ms\python.exe -m pytest --tb=short -q
npm test
npm run lint
npm run build
```

## Findings

| Severity | Area | Status | Evidence | Impact | Recommendation |
|---|---|---|---|---|---|
| High | Image upload and ML denial of service | Partially mitigated | Backend now validates PNG/JPEG/WebP dimensions before forwarding, keeps the 10 MB limit, and enforces a per-user hourly edit limit. Segmentation still performs expensive decode/CV/OpenAI work. | A valid but adversarial image can still consume CPU/GPU/memory or create costly OpenAI calls, but oversized-dimension and repeated-request paths are reduced. | Consider full image decode validation, lower pixel limits, persistent cross-instance quotas, and per-IP rate limits. |
| High | Segmentation service auth fallback | Mitigated in code and deploy workflow | `REQUIRE_SEGMENTATION_IAM` now lets production fail closed if the backend cannot fetch a Cloud Run identity token. `.github/workflows/deploy.yml` sets `REQUIRE_SEGMENTATION_IAM=true` for `car-backend-ms`. Default remains false for local development. | Production avoids silent unauthenticated fallback once the new revision is deployed. | Validate `SEGMENTATION_MS_URL` is HTTPS and keep the segmentation Cloud Run service IAM-protected. |
| Medium | Segmentation response size and memory pressure | Partially mitigated | Backend now validates required response fields, base64 correctness, and decoded payload size before using `result_b64` and `mask_b64`. | Base64 JSON overhead remains, but malformed or oversized responses are rejected earlier. | Prefer multipart response, streaming binary, or storage-backed transfer. |
| Medium | OpenAI cost and abuse controls | Partially mitigated | Backend now has `EDIT_PHOTO_RATE_LIMIT_PER_HOUR` for per-user in-memory request limiting. | One backend instance now has a safety valve, but limits are not shared across instances or durable across restarts. | Add persistent per-user quotas, per-IP throttles, and cost telemetry. |
| Medium | Firebase Storage path and authorization assumptions | Partially mitigated | `storage_service.upload_photo()` now validates role names and attaches owner/role metadata. Firebase Storage rules already live in `car-frontend/storage.rules` and deny direct user writes. | DB ownership checks and backend-only writes reduce direct storage abuse risk. | Add Firebase emulator rule tests in CI and monitor bucket IAM drift. |
| Medium | Mask/original retention and privacy | Backend now stores original, result, and mask images in Firebase Storage. Masks can reveal user image structure and edited target areas. | Retained masks and originals increase privacy exposure if bucket rules, service accounts, or DB paths are compromised. | Define retention policy for originals and masks; consider deleting masks after debugging windows; document user data lifecycle. |
| Medium | Dependency audit gap for local Python services | Mitigated for new installs | `pip-audit` is now listed in both Python services' `requirements-test.txt`; existing local envs must be updated. | Fresh dev/test envs can run local Python advisory scans. | Recreate or update local Conda envs before running `python -m pip_audit`. |
| Medium | Supply-chain risk from Git dependency | `car-segmentation-ms/requirements.txt` installs `segment-anything` directly from GitHub by commit SHA. | Commit pinning is good, but GitHub availability and repository trust become part of the build chain; hashes are not enforced like wheel hashes. | Vendor a reviewed wheel/artifact or use hash-checked dependency installation for release builds. Track upstream security updates manually. |
| Medium | Container image hardening | Backend and segmentation Dockerfiles create non-root users, but images do not set `HEALTHCHECK`, read-only filesystem guidance, dropped Linux capabilities, or image digest pinning. | Runtime blast radius and reproducibility can be improved, especially for internet-facing backend and GPU service. | Pin base images by digest for production, add health/readiness checks where supported, run with read-only root FS except writable temp dirs, and drop capabilities in deployment settings. |
| Medium | CI/CD deploy credential handling | `.github/workflows/deploy.yml` authenticates with a long-lived JSON service account key from `GCP_SA_KEY`. Actions are pinned by commit in PR checks/deploy, which is good. | Long-lived deploy keys are high-value secrets; compromise grants broad deploy powers until rotated. | Move to GitHub OIDC Workload Identity Federation for GCP deploys. Keep commit-pinned actions and restrict deploy environment approvals. |
| Low | Frontend CSP allows inline styles | `car-frontend/nginx.conf` sets CSP with `style-src 'self' 'unsafe-inline'`. | Inline styles weaken CSP and can help some XSS payloads if another injection exists. | Move toward nonce/hash-based styles if feasible. If Tailwind/runtime constraints require inline styles, document the exception. |
| Low | Frontend security headers incomplete | Mitigated for Nginx and Firebase Hosting | `nginx.conf` includes CSP, HSTS, Permissions-Policy, nosniff, referrer policy, and frame protections. `car-frontend/firebase.json` now sets equivalent headers for the Firebase Hosting deployment path. | Browser protections now apply to the current Firebase-hosted frontend as well as the Docker/Nginx image. | Revisit CSP later to remove `unsafe-inline` if the app can support nonce/hash-based styles. |
| Low | Broad exception swallowing in metadata token fetch | Partially mitigated | `_identity_token()` now catches `httpx.HTTPError`; production can fail closed through `REQUIRE_SEGMENTATION_IAM`. | Metadata/auth failures are less broadly swallowed, but explicit logging is still missing. | Add structured warning logs without token contents. |
| Low | Prompt/content policy and logging visibility | Prompts are stored in `operation_params`; no explicit prompt moderation, redaction, or abuse-event logging is visible. | Stored prompts may contain sensitive user text; malicious prompts can be replayed or inspected by operators. | Add privacy notice/retention rules for prompts, redact logs, and consider abuse monitoring. |
| Low | Generated build artifacts in repo scan surface | Static scans encountered `car-frontend/dist` and local cache/output folders unless explicitly excluded. | Audits become noisy and can accidentally inspect generated bundles instead of source. | Ensure generated frontend `dist/`, ML `output/`, and caches are gitignored and excluded from audit commands. |
| Low | Image edit preservation quality | Mitigated | Background prompts previously included composition-changing language such as reframing/low-angle shots, and exact SAM masks could leave car-edge pixels editable. Segmentation now expands the protected car mask for background edits, and the OpenAI edit call uses `input_fidelity="high"`. | Reduces the risk that a background edit repaints the car smaller, moved, or redrawn. | Continue reviewing saved `mask.png` samples from production failures; adjust the mask margin if specific cars still get edge repainting. |

## Dependency Audit Results

| Component | Command | Result |
|---|---|---|
| Frontend | `npm audit --json` in `car-frontend` | Passed again with 0 vulnerabilities across 442 total dependencies. |
| Backend Python | `python -m pip_audit -r requirements.txt` in `car-backend-ms` | Initial run failed locally: `No module named pip_audit`. `pip-audit` is now in `requirements-test.txt`; rerun after updating the Conda env. |
| Segmentation Python | `python -m pip_audit -r requirements.txt` in `car-segmentation-ms` | Initial run failed locally: `No module named pip_audit`. `pip-audit` is now in `requirements-test.txt`; rerun after updating the Conda env. |
| Secret scan | `gitleaks detect --source . --redact --verbose` | Not run locally: `gitleaks` was not installed on PATH. CI installs and runs Gitleaks in `pr-checks.yml`. |

## Operational And Deployment Improvements

- Keep `REQUIRE_SEGMENTATION_IAM=true` in production and consider adding a broader `ENVIRONMENT=production` setting for future production-only checks.
- Add Firebase Storage emulator tests for the existing `car-frontend/storage.rules`, then run them in CI.
- Add structured security logs around denied uploads, segmentation failures, OpenAI failures, quota/rate-limit events, and image-preservation retries.
- Add persistent cost controls for GPU/OpenAI calls: durable per-user quotas, request throttling, and dashboards.
- Prefer GCP Workload Identity Federation over JSON service account keys in GitHub Actions.
- Add dependency update automation with grouped PRs and mandatory audit pass.
- Consider SBOM generation and image vulnerability scanning for Docker images.
- Document data retention for original photos, generated images, masks, and prompts.

## Prioritized Remediation Checklist

1. Backend: replace in-memory edit rate limiting with durable cross-instance quotas.
2. Segmentation: replace base64 JSON image return with a lower-overhead response format.
3. Storage: add emulator-based tests for Firebase Storage rules.
4. CI/CD: replace `GCP_SA_KEY` with Workload Identity Federation.
5. Dependencies: update local Conda envs and rerun `pip-audit`.
6. Frontend: remove `unsafe-inline` from CSP if feasible.
7. Docker/Cloud Run: pin base image digests and document runtime hardening settings.
8. Privacy: define retention rules for originals, results, masks, and prompts.
9. Observability: add structured security/cost logs for denied uploads, quotas, and provider failures.
10. Image quality: track failed background edits and preserve representative `mask.png` artifacts for short-lived debugging.

## Limitations

- This is a static and tooling-assisted review, not a penetration test.
- Python dependency advisories were not checked locally because `pip_audit` is not installed in the active Conda environments.
- Local secret scanning was not completed because `gitleaks` is not installed on PATH.
- No live GCP/Firebase IAM, bucket rules, Secret Manager permissions, or Cloud Run settings were queried from this environment.
