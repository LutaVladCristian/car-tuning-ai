# Security & Documentation Review (2026-04-14)

## Scope Reviewed

### Code
- `car-backend-ms/` (FastAPI auth + proxy + persistence)
- `car-segmentation-ms/` (FastAPI ML service)
- `car-frontend/src/` (React SPA auth/api flows)

### Documentation
- `.claude/CLAUDE.md`
- `.claude/docs/car-backend-ms.md`
- `.claude/docs/car-frontend.md`
- `.claude/docs/car-segmentation-ms.md`

Excluded as requested:
- `.claude/docs/code-review.md`

---

## Executive Summary

The project is in a **better-than-average state for an early-stage AI product**, with good fundamentals already present:
- backend-side upload size and magic-byte validation before forwarding to ML service,
- JWT expiry enforcement,
- protected photo history endpoints,
- narrowed CORS config by environment.

The main residual risks are not “code execution” class issues, but **auth hardening, service exposure boundaries, and operational abuse controls**:
1. **No login/register rate limiting** (brute-force and account enumeration pressure).
2. **JWT signing key is process-generated at startup**, so tokens are invalidated on restart and key management/rotation is not controlled.
3. **Frontend token storage in `localStorage`** keeps UX simple but increases blast radius if XSS ever appears.
4. **Segmentation MS has no independent input guards** (size/type) and no auth if exposed directly.
5. **Some docs are stale or optimistic** versus current code (could mislead deployment decisions).

---

## Findings by Severity

## High

### H-1: Missing auth endpoint rate limiting / abuse controls
**Where:** `POST /auth/login`, `POST /auth/register` paths exist with no throttling hooks/middleware in backend.

**Risk:** Attackers can automate password guessing and registration abuse at high volume, which can lead to account compromise, higher infra cost, and noisy logs.

**Evidence:** Auth routes have validation and password verify, but no IP/user throttling, delay, CAPTCHA challenge, or lockout behavior.

**Recommendation (practical):**
- Add lightweight rate limits at edge/reverse proxy (preferred first step):
  - `/auth/login`: e.g., 5/min per IP + username tuple, burst 10.
  - `/auth/register`: e.g., 3/min per IP.
- Return generic error body for rate-limited auth attempts.
- Add alerting for repeated 401 bursts.

---

## Medium

### M-1: JWT secret is ephemeral (generated each process start)
**Where:** backend security module sets `JWT_SECRET_KEY = secrets.token_hex(32)` on import.

**Risk:** All active tokens become invalid after restart/deploy; prevents predictable key lifecycle and complicates incident response/rotation policy.

**Why this matters:** This is more of a **security-operability flaw** than direct exploit. Teams need deterministic secret management for stable auth and emergency key rotation.

**Recommendation:**
- Load signing key from environment/secret manager (`JWT_SECRET_KEY`).
- Support key versioning (kid) when feasible.
- Keep short-lived access tokens (already done), then optionally add refresh tokens later.

### M-2: JWT claims are minimal (`sub`, `exp`) with no `iss`/`aud`
**Where:** token create/decode currently checks expiration and subject.

**Risk:** In multi-service evolution, weak claim scoping can allow token confusion between environments/services.

**Recommendation:**
- Add `iss` and `aud` claims now (low effort).
- Validate both in decode path.

### M-3: Frontend stores bearer token in `localStorage`
**Where:** frontend auth context and axios interceptor read/write `car_tuning_token` from `localStorage`.

**Risk:** If any XSS bug appears in future, attacker can exfiltrate token and impersonate user until expiry.

**Recommendation (balanced, not overkill):**
- Near-term: keep as-is but enforce stronger CSP + dependency hygiene + strict input escaping standards.
- Mid-term: migrate to HttpOnly Secure SameSite cookies if backend/frontend deployment architecture supports it cleanly.

### M-4: Segmentation service has no auth and trusts network boundary
**Where:** segmentation docs explicitly state “No auth”.

**Risk:** If Cloud Run/service ingress is accidentally public, heavy endpoints become abuse targets (cost DoS, model abuse).

**Recommendation:**
- Enforce private ingress / internal-only networking at platform level.
- Optionally require shared service token header from backend to segmentation service.

### M-5: Segmentation service lacks local file-size/type hard checks
**Where:** segmentation endpoints read uploaded file directly; backend has validation, segmentation MS itself does not.

**Risk:** If segmentation endpoint is accessed directly (misconfig, internal misuse), large or invalid payloads can consume memory/CPU unexpectedly.

**Recommendation:**
- Duplicate guardrails in segmentation MS:
  - max upload size (same 10MB),
  - magic byte validation for allowed image types,
  - reject malformed images early.

### M-6: Storing image blobs in SQL can become security+availability risk at scale
**Where:** backend `Photo` model stores original/result images in `LargeBinary` columns.

**Risk:** DB bloat, backup growth, longer restore windows, and easier accidental data overexposure through DB-level access.

**Recommendation:**
- Move binaries to object storage (GCS/S3) and keep only metadata + signed URL references in DB.
- Use lifecycle/retention policy for old artifacts.

---

## Low

### L-1: Dependency hygiene inconsistency
**Where:** backend pins older packages (`passlib==1.7.4`, `python-jose==3.3.0`), segmentation requirements are mostly unpinned.

**Risk:** Increased chance of known CVEs or supply-chain drift over time.

**Recommendation:**
- Add scheduled dependency update cadence (monthly or biweekly).
- Introduce `pip-audit`/`safety` in CI for Python, and npm audit policy for frontend.

### L-2: Error-message consistency could leak minor behavior details
**Where:** auth returns “Invalid username or password” (good), but other endpoints return detailed upstream status context.

**Risk:** Minor information disclosure; mostly acceptable for internal diagnostics.

**Recommendation:**
- Keep detailed errors in server logs; consider generic client message with trace/correlation id in prod.

---

## Documentation Review (non-code)

## Good
- Architecture boundaries and service responsibilities are clearly documented.
- Backend/segmentation/frontend docs are readable and map to folders well.
- Environment setup and model artifacts are clearly listed.

## Gaps / Corrections needed

1. **Stale CORS statement in `.claude/CLAUDE.md`**
   - It says CORS is hardcoded to localhost.
   - Current code uses `settings.CORS_ORIGINS` from config.
   - Update this note to avoid wrong deployment assumptions.

2. **Frontend test coverage statement is outdated**
   - Doc says tests currently cover prompt construction and reducer behavior.
   - Repo now includes many auth/component/hook tests.
   - Expand docs so contributors trust coverage surface.

3. **Segmentation doc says OpenAI errors propagate as HTTP 500**
   - True at high-level, but would benefit from explicit note on timeout/retry behavior and expected failure payload format.

4. **Security controls not explicitly documented**
   - Add a short “Security Posture” section per service:
     - auth/session model,
     - ingress assumptions,
     - max payload sizes,
     - accepted content types,
     - secrets source,
     - logging/redaction expectations.

---

## Prioritized Improvement Plan (lean, non-overkill)

### Phase 1 (1–2 days)
1. Move JWT secret to env/secret manager (`JWT_SECRET_KEY`).
2. Add login/register rate limiting at ingress/API gateway.
3. Add segmentation-side file size/type validation (defense in depth).
4. Fix stale `.claude` docs (CORS note + frontend test coverage note).

### Phase 2 (next sprint)
1. Add JWT `iss`/`aud` claims and verification.
2. Add security audit jobs (`pip-audit`, npm audit policy).
3. Add structured security logging for auth failures and upstream segmentation failures.

### Phase 3 (when scaling)
1. Migrate image blobs out of SQL to object storage.
2. Consider cookie-based auth token transport if threat model requires stronger browser-side token protection.

---

## What does *not* look overkill right now
- Keep current JWT+Bearer architecture; harden it incrementally.
- Avoid introducing full OAuth provider migration immediately unless product requirements demand SSO.
- Keep segmentation service simple; just add baseline guardrails and strict ingress controls.

---

## Final Assessment

Current code is **functional and relatively clean**, with several earlier issues already mitigated (notably backend upload validation and CORS configurability). The highest value remaining work is **abuse resistance and secret management hardening**, plus **documentation freshness** so deployment/security assumptions remain accurate.
