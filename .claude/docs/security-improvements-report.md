# Security And Improvement Report

Generated: 2026-04-26

Remediation update: the initial findings in this report were implemented after
the scan. The current codebase now includes backend prompt/size validation,
segmentation image dimension checks, generic Firebase auth errors, non-root
runtime containers, pinned segmentation dependencies, CI dependency/security
scanning, frontend security headers, and backend-only Firebase Storage writes.

## Executive Summary

This repository contains a three-service AI car image editing platform:

- `car-frontend`: React/Vite SPA using Firebase Authentication and Axios.
- `car-backend-ms`: FastAPI gateway that verifies Firebase ID tokens, persists photo metadata, stores images in Firebase Storage, and proxies edit requests.
- `car-segmentation-ms`: FastAPI ML service that runs YOLO/SAM preprocessing and sends masked image edits to OpenAI.

The main trust boundaries are the browser-to-backend API, backend-to-segmentation service call, Firebase/Google Cloud service integrations, user-uploaded image processing, and CI/CD credentials. The current implementation has several useful controls already in place, but the highest-value improvements are stricter public API validation, safer image decoding limits, less verbose auth errors, stronger container hardening, and dependency/secret scanning in CI.

## Confirmed Protections

- Firebase ID tokens are verified by `firebase-admin` before protected backend endpoints resolve a user.
- Photo listing and download routes filter by both `photo_id` and `current_user.id`, limiting cross-user access through the backend.
- `/edit-photo` in `car-backend-ms` rejects files larger than 10 MB and checks image magic bytes for JPEG, PNG, and WEBP before proxying.
- Backend CORS origins are environment-driven through `CORS_ORIGINS`, with a narrow local default.
- Backend-to-segmentation calls can attach a GCP-signed identity token for IAM-protected Cloud Run invocation.
- Segmentation uses per-request temporary output directories and cleans them up after OpenAI processing.
- Segmentation returns HTTP 503 until model loading is complete.
- Firebase Storage rules restrict paths under `users/{userId}/photos/**` to authenticated users whose UID matches the path.
- Frontend dependency audit currently reports 0 known vulnerabilities through `npm audit --json`.

## Findings

### High

1. Public API validation is incomplete for `prompt` and `size`.
   - Affected: `car-backend-ms/app/routers/segmentation.py`
   - The backend accepts arbitrary `prompt` and `size` form values and forwards them to the segmentation service. The segmentation service has a prompt length cap and partial size validation later in the pipeline, but the public gateway should reject invalid values before consuming ML/API resources.
   - Recommendation: add backend-side constraints for prompt length, blank prompt rejection, and an explicit allowlist for OpenAI-supported sizes or `auto`.

2. Image decompression and pixel limits are not enforced before decode.
   - Affected: `car-segmentation-ms/server.py`, `car-segmentation-ms/segmentation.py`
   - The backend enforces byte size and magic bytes, but segmentation still decodes user-controlled image data with PIL/OpenCV before strong dimension or pixel-count checks. A small compressed image can expand to a very large bitmap and exhaust memory.
   - Recommendation: set PIL decompression-bomb limits, verify images after opening, reject images above a max width/height/pixel count, and mirror the same constraints before OpenCV decoding.

3. Invalid image decode failures are not consistently converted to clean 4xx responses.
   - Affected: `car-segmentation-ms/server.py`, `car-segmentation-ms/segmentation.py`
   - `PIL.Image.open(...)` and `cv2.imdecode(...)` failures can currently surface as generic 500s depending on where the failure happens.
   - Recommendation: catch PIL decode/verify errors and OpenCV decode failures, returning HTTP 400 or 415 with a generic client-safe message.

### Medium

4. Firebase auth errors leak exception details.
   - Affected: `car-backend-ms/app/routers/auth.py:21`
   - `/auth/firebase` returns `Invalid Firebase token: {exc}`, which can disclose provider error details to clients.
   - Recommendation: return a generic `Invalid or expired token` message and log the internal exception server-side if needed.

5. Auto-created users can have an empty email.
   - Affected: `car-backend-ms/dependencies.py`
   - `get_current_user()` auto-creates users with `claims.get("email", "")`. If a verified token lacks an email claim, multiple users can collide on the unique `email` column, causing 500s and fragile account state.
   - Recommendation: require an email claim for user creation, use a nullable email field, or change the uniqueness model to handle providers without email.

6. Containers run as root by default.
   - Affected: `car-backend-ms/Dockerfile`, `car-segmentation-ms/Dockerfile`, `car-frontend/Dockerfile`
   - None of the Dockerfiles define a non-root runtime user.
   - Recommendation: create and switch to a least-privileged user in each runtime image, ensuring writable directories such as segmentation `model/` and `output/` have correct ownership.

7. Segmentation dependency supply chain is loosely pinned.
   - Affected: `car-segmentation-ms/requirements.txt`
   - Many packages are unpinned, and `segment-anything` is installed directly from GitHub without a commit SHA.
   - Recommendation: pin direct dependencies, pin Git dependencies to immutable commits, and generate lock files for deployment builds.

8. CI lacks vulnerability and secret scanning.
   - Affected: `.github/workflows/pr-checks.yml`, `.github/workflows/deploy.yml`
   - CI runs lint/build/test but does not run Python dependency auditing, secret scanning, or action pinning checks. GitHub Actions are version-tagged rather than pinned to commit SHAs.
   - Recommendation: add `pip-audit` or a comparable scanner for both Python services, add secret scanning such as Gitleaks, and consider pinning third-party actions by SHA.

### Low

9. Frontend static hosting lacks common browser security headers.
   - Affected: `car-frontend/nginx.conf`
   - The Nginx config sets long-lived immutable caching for static assets but does not set headers such as `Content-Security-Policy`, `X-Content-Type-Options`, `Referrer-Policy`, or frame protection.
   - Recommendation: add a CSP compatible with Firebase/Auth/OpenAI API usage, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, and `X-Frame-Options` or CSP `frame-ancestors`.

10. Firebase Storage rules allow direct client writes to photo paths.
    - Affected: `car-frontend/storage.rules`
    - Rules allow authenticated users to write under their own photo path. Current app flow writes through the backend, so direct client writes are broader than necessary unless planned for future uploads.
    - Recommendation: prefer backend-only writes via Admin SDK, or add strict path, content type, and size rules if direct client uploads become intentional.

## Prioritized Remediation

1. Add backend validation for `prompt` and `size` before proxying to segmentation.
2. Add image dimension/pixel-count safeguards and explicit decode error handling in segmentation.
3. Replace verbose Firebase token errors with generic client-facing 401 responses.
4. Decide the account model for Firebase tokens without email claims and update DB/schema handling accordingly.
5. Run all containers as non-root and adjust filesystem ownership for writable runtime directories.
6. Pin segmentation dependencies and Git-based installs to immutable versions.
7. Add Python dependency auditing and secret scanning to PR checks.
8. Add frontend security headers for Nginx/Firebase-hosted static assets.
9. Tighten Firebase Storage write rules if client-side direct uploads are not a product requirement.

## Verification Notes

Commands run:

```powershell
npm audit --json
```

Result from `car-frontend`: 0 vulnerabilities across 442 total dependencies.

```powershell
pip-audit -r requirements.txt
```

Result from both `car-backend-ms` and `car-segmentation-ms`: could not run locally because `pip-audit` is not installed:

```text
pip-audit : The term 'pip-audit' is not recognized as the name of a cmdlet, function, script file, or operable program.
```

Recommendation: add `pip-audit` to CI or run it from a controlled Python tooling environment so backend and segmentation dependency exposure is continuously checked.

## Assumptions

- The existing `.claude/docs/` directory is the documentation destination.
- Existing uncommitted files are treated as the current state and were not reverted.
