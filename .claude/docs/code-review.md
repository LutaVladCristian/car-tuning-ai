# Code Review — car-tuning-ai

**Date:** 2026-04-14  
**Branch:** main-to-deploy-version-1  
**Scope:** All three services — car-backend-ms, car-segmentation-ms, car-frontend

---

## Critical

| # | Service | File | Issue |
|---|---------|------|-------|
| C1 | segmentation-ms | `server.py:79-80` | **File handles never closed** — `open(image_path, "rb")` passed directly to OpenAI without a context manager. After ~1024 requests the OS file descriptor table exhausts and the service crashes. |
| C2 | segmentation-ms | `server.py:59-81` | **Prompt injection** — user-supplied `prompt` is passed to OpenAI with zero sanitization or length limits. |
| C3 | segmentation-ms | `server.py` + `segmentation.py:13` | **Race condition on shared `output/` directory** — all concurrent requests overwrite the same `image.png` / `mask.png`. Request A's OpenAI call can end up using Request B's mask. |
| C4 | backend-ms | `app/db/models/photo.py:28-29` | **Images stored as `LargeBinary` in PostgreSQL** — original + result images for every operation bloat the DB, slow every query that touches the table, and will cause memory exhaustion at scale. Should use object storage (GCS/S3) with only a URL column. |
| C5 | backend-ms | `app/routers/segmentation.py:23,54,86` | **No file size limit** — `await file.read()` has no cap. An attacker can upload gigabytes, exhausting server memory (DoS). |
| C6 | frontend | `context/AuthContext.tsx:8-9,16-17` | **JWT stored in `localStorage`** — readable by any JS on the page. XSS → full account takeover. Should use `httpOnly` + `Secure` + `SameSite=Strict` cookies set by the backend. |
| C7 | backend-ms | `main.py:14` | **CORS hardcoded to `localhost:5173`** — blocks all production requests. Must be env-var driven. |

---

## High

| # | Service | File | Issue |
|---|---------|------|-------|
| H1 | segmentation-ms | `segmentation.py:43-46,84-85` | **Return type inconsistency crashes the server** — `segment_car()` and `segment_car_part()` return `{"message": "..."}` when no car/part is detected, but `server.py` calls `Image.fromarray()` on the return value → `TypeError` / 500. Should raise `HTTPException(400, ...)` instead. |
| H2 | segmentation-ms | `segmentation.py:19-22` | **Hardcoded relative model paths** — fails immediately if the service is started from any directory other than `car-segmentation-ms/`. Should use `Path(__file__).parent / "model" / ...`. |
| H3 | segmentation-ms | `utils.py:28-61` | **Temp files never cleaned up** — `output/image.png` and `output/mask.png` are written but never deleted. Disk fills up over time; also worsens the C3 race condition. |
| H4 | backend-ms | `app/routers/auth.py:13-37` | **No rate limiting on `/auth/login` and `/auth/register`** — trivially brute-forced or spam-registered. Add `slowapi` or equivalent. |
| H5 | backend-ms | `app/routers/segmentation.py:23,54,86` | **No file type validation** — MIME type and magic bytes are never checked. Arbitrary files are forwarded to the ML service and stored in the DB. |
| H6 | backend-ms | `app/core/security.py:28` | **JWT expiry may not be enforced** — `python-jose` may skip `exp` validation depending on version. Add `options={"verify_exp": True}` explicitly. |
| H7 | backend-ms | `alembic/versions/45e90066957a_db_setup_v1.py:43` | **No `ON DELETE CASCADE` on `photos.user_id`** — deleting a user leaves orphaned photo rows (or raises a FK constraint error). |
| H8 | frontend | `hooks/useEditPhoto.ts:32-48` | **Race condition in polling** — the "before" photo count snapshot is taken, then `/edit-photo` blocks for up to 180 s. A different user's photo inserted during that window will be mistaken for the current result. The server should return the new photo ID directly. |
| H9 | frontend | `hooks/useEditPhoto.ts:41-48` | **Polling silently succeeds with no result** — if the DB write takes > 5 s, polling exits with `newId = null` and still shows a success message. Users are told "check your history" but the result may not exist yet. |
| H10 | frontend | `components/tuning/ImageSelector.tsx:26` | **`URL.createObjectURL` never revoked** — every uploaded file leaks a blob URL. Memory accumulates across uploads. Call `URL.revokeObjectURL()` on cleanup / new upload. |
| H11 | frontend | `components/results/ResultDisplay.tsx:30` | Same blob URL leak as H10, on every photo result loaded. |
| H12 | frontend | `hooks/usePhotoHistory.ts:31` | **Bare `catch {}` swallows errors** — error details are lost, making failures invisible to the user and to debugging. |

---

## Medium

| # | Service | File | Issue |
|---|---------|------|-------|
| M1 | segmentation-ms | `utils.py:31` | **Unvalidated `size` parameter** — `size.split("x")` + `int()` with no bounds check. Malformed input crashes; a huge size causes OOM. Validate format and cap dimensions. |
| M2 | segmentation-ms | `server.py:42` | **`carPartId` not validated** — no documented range; invalid IDs silently return empty results, indistinguishable from "part not found". |
| M3 | backend-ms | `app/db/session.py:7` | **`"sqlite" in url` detection is fragile** — a Postgres URL containing the string `sqlite` would be misidentified. Use `url.startswith("sqlite")` or parse the scheme. |
| M4 | backend-ms | `app/db/session.py:9-12` | **No SQLAlchemy connection pool config** — default pool of 5 is too small under any real load. Set `pool_size` and `max_overflow` explicitly. |
| M5 | backend-ms | `app/routers/auth.py:14-17` | **Two separate queries for duplicate check** — one `OR` query is more efficient and avoids a TOCTOU window. |
| M6 | backend-ms | `app/routers/photos.py:22-24` | **Two queries for paginated list** — `query.count()` + `query.all()` hits the DB twice. Use a window function or a single count subquery. |
| M7 | backend-ms | `app/services/proxy_service.py` | **All 4xx/5xx from segmentation MS become 502** — a 400 ("no cars detected") should become a 400 or 422 to the client, not a generic gateway error. Map status codes explicitly. |
| M8 | backend-ms | `app/services/proxy_service.py` | **Duplicate code** — the three `forward_*` functions are near-identical. Extract a shared `_forward(path, form_data, timeout)` helper. |
| M9 | frontend | `hooks/useEditPhoto.ts:17,36,42` | **Magic numbers** — `500` ms sleep, `180000` ms timeout, `10` retries are scattered inline. Extract to named constants. |
| M10 | frontend | `components/tuning/ImageSelector.tsx:29` | **No file size validation** — only MIME type is checked. Large files hit API limits with no user feedback. Add a cap (e.g., 10 MB). |
| M11 | frontend | `components/tuning/tuningReducer.ts:28-39` | **Unsafe `as keyof` casts** — `action.field as keyof typeof state.car` bypasses TypeScript's type system. An invalid field name silently writes to an unintended key. Use a discriminated union with explicit field types. |
| M12 | frontend | `api/client.ts:15-25` | **Axios 401 interceptor clears `localStorage` directly** — should call `logout()` from `AuthContext` instead to keep auth state and storage in sync. |
| M13 | frontend | `components/prompt/PromptPreview.tsx` | **No prompt length limit** — user-typed custom prompts hit the OpenAI API uncapped. Add `maxLength` on the textarea and a character counter. |

---

## Low / Code Quality

| # | Service | File | Issue |
|---|---------|------|-------|
| L1 | backend-ms | `main.py:16-17` | `allow_methods=["*"], allow_headers=["*"]` — unnecessarily broad CORS. Restrict to `["GET","POST"]` and the headers actually used. |
| L2 | backend-ms | `app/db/models/photo.py` | Missing `cascade="all, delete-orphan"` on the `User.photos` relationship (ORM level to complement the DB-level fix in H7). |
| L3 | backend-ms | `app/schemas/photo.py` | `user_id` exposed in `PhotoResponse` is an unnecessary internal detail for clients. |
| L4 | backend-ms | `requirements.txt` | `passlib==1.7.4` (2013) and `python-jose==3.3.0` are outdated — upgrade to get security patches. |
| L5 | segmentation-ms | `environment-local.yml` | Most non-PyTorch pip deps are unpinned — non-deterministic builds across environments. |
| L6 | frontend | `pages/TuningPage.tsx:48-51` | `handleHistorySelect` is defined but its body is a comment stub — dead code. |
| L7 | frontend | `components/auth/LoginForm.tsx` vs `SignUpForm.tsx` | Inconsistent error parsing — `SignUpForm` handles validation error arrays; `LoginForm` doesn't. Unify into a shared `parseApiError()` helper. |
| L8 | frontend | `App.tsx` | No error boundary — a single component render crash takes down the entire app. |
| L9 | frontend | All components | No `aria-live` regions for async status changes; hidden file input has no `aria-label`. Screen reader support is absent. |
| L10 | frontend | `api/client.ts:4` | `VITE_API_BASE_URL` silently defaults to `localhost` if unset in production — should log a warning in non-dev builds. |

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | 7 |
| High | 12 |
| Medium | 13 |
| Low | 10 |
| **Total** | **42** |

---

## Top 5 to Fix First

1. **C3 + H3** — Shared `output/` directory race condition + no temp file cleanup. Every concurrent request corrupts another's result. Fix: generate a per-request temp directory (`tempfile.mkdtemp()`), clean up in a `finally` block.
2. **C4 + H5** — Images stored in the DB as blobs with no file type validation. Fix: migrate to GCS/S3 object storage, store only URLs; validate MIME type and magic bytes on upload.
3. **C1** — File handles leaked to OpenAI. Fix: use `with open(...) as f` and pass `f`.
4. **C6** — JWT in `localStorage`. Fix: move auth to `httpOnly` cookies (requires backend change too).
5. **H1** — `segment_car()` / `segment_car_part()` return a `dict` on failure but the caller does `Image.fromarray(dict)` → 500. Fix: raise `HTTPException(400, detail="No cars detected")` and remove the dict return path.
