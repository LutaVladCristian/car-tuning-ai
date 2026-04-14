# Security And Documentation Review Report Plan

## Summary

Create a new Markdown report at `.claude/docs/security-code-doc-review.md` containing a full security-focused review of the tracked codebase and `.claude` documentation.

Scope:
- Review all tracked backend, frontend, segmentation, CI/config, tests, dependency manifests, README, and `.env.example`.
- Review `.claude/CLAUDE.md`, `.claude/docs/car-backend-ms.md`, `.claude/docs/car-frontend.md`, and `.claude/docs/car-segmentation-ms.md`.
- Exclude `.claude/docs/code-review.md` exactly as requested.
- Do not read or quote real `.env` secrets; only note that `.env` is gitignored.

## Key Report Content

- Organize findings by severity: Critical, High, Medium, Low, and Documentation Drift.
- Include exact file references and concise evidence for each finding.
- Capture likely current findings, including:
  - `JWT_SECRET_KEY` is generated at import/startup in backend security code, invalidating tokens on restart and preventing multi-instance deployments; recommend env/Secret Manager-backed secret with rotation plan.
  - JWT is stored in frontend `localStorage`; recommend httpOnly, Secure, SameSite cookies when production hardening is needed.
  - Login/register have no rate limiting; recommend small, targeted throttling rather than a broad anti-abuse system.
  - Uploaded images are stored as SQL `LargeBinary`; acceptable for prototype, but recommend object storage before production.
  - Backend reads whole uploads into memory before size validation; acceptable with current 10 MB cap but streaming enforcement would be stronger.
  - Segmentation service has no direct auth and must remain private/internal; document network boundary requirements.
  - Dependency risk: Python segmentation dependencies are loosely pinned and include a GitHub dependency; recommend pinning hashes/refs where practical and running audits.
  - Frontend nginx config lacks common security headers; recommend a small header set if served directly by nginx.
  - CI segmentation job tolerates pytest exit code 5; verify whether this is still needed or masking missing tests.
- Clearly mark items already fixed compared with stale doc claims, such as env-driven CORS and per-request temp directories, without using `.claude/docs/code-review.md` as a source.

## Documentation Review

- Add a "Documentation drift" section noting stale or misleading docs:
  - `.claude/CLAUDE.md` still says backend CORS is hardcoded, while current code reads `settings.CORS_ORIGINS`.
  - `.claude/docs/car-segmentation-ms.md` still says `/edit-photo` writes fixed `output/image.png` and `output/mask.png`, while current code uses per-request temp directories.
  - Several `.claude` docs contain mojibake/encoding artifacts in diagrams and punctuation; recommend rewriting or normalizing to UTF-8 text.
- Suggest lightweight doc improvements:
  - Add production security checklist: secret storage, private segmentation networking, auth token storage, rate limits, object storage, dependency audits.
  - Add "prototype vs production" notes so recommendations do not become over-engineered for local development.

## Validation

- Run non-mutating checks where available:
  - `npm run lint`, `npm test`, and `npm run build` in `car-frontend`.
  - Backend pytest via the existing environment command if available.
  - Segmentation pytest via the existing environment command if available.
  - Dependency audits such as `npm audit` and Python audit tooling if installed or approved for network access.
- If a command cannot run because dependencies, envs, model files, network, or permissions are missing, record that limitation in the report instead of blocking the report.