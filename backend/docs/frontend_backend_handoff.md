# Backend handoff for frontend integration

This branch contains the backend changes from `feature/ci-logging-debug`, based on the locally available `origin/develop` commit. It is intended to let frontend work proceed against the updated API without taking the frontend files from the conflicted feature branch.

## What changed

- Added the NISR official yield history, provenance and evaluation artifacts, yield intervals, explanations, and district priority evidence.
- Added paginated zone and agricultural metric retrieval and zone identity safeguards. Use the paginated endpoints for large result sets; do not reproduce backend duplicate-resolution logic in the UI.
- Expanded decision evidence, AI assistant context, planning/resource calculations, community posts and field observations, admin access, and communication workflows.
- Added WhatsApp Cloud API webhook, opt-in/consent, templates, delivery, and admin APIs. The default provider is `mock`; live sending requires deliberate configuration and approved Meta assets/templates.
- Added database migrations `0002` through `0013` alongside the existing `0001` migration. Apply them in order in an environment that has not already applied them; check the migration ledger first to avoid reapplying schema changes.

## Main API groups

The FastAPI app mounts these route groups (OpenAPI is available at `/docs` when the API is running):

| Purpose | Prefix | Useful routes |
| --- | --- | --- |
| Decision evidence | `/decision` | `GET /crops`, `GET /evidence-ranking`, `GET /district-ranking`, `POST /predict`, `GET /recommendations/{zone_id}` |
| Segmentation and retrieval | `/segmentation` | `GET /districts`, `GET /zones/page`, `GET /zones/summary`, `GET /agri-metrics/page`, `GET /crop-comparison/{district}` |
| Planning | `/planification` | `GET /resources/{zone_id}`, `POST /roadmap`, `GET /plans/{zone_id}` |
| Assistant and crop health | `/chat` | `POST /`, `POST /disease-detect`, `POST /disease-detect-upload` |
| Community | `/community` | register/login, `GET/POST /posts`, comments, field reports, moderation |
| Communication and WhatsApp | `/communication`, `/webhooks` | contact/alerts, WhatsApp status/info, consent/subscriptions, delivery, `GET/POST /webhooks/whatsapp` |
| Admin | `/auth/admin`, `/admin` | admin login/account and protected operational endpoints |

Use the route schemas in `/docs` as the source of truth for request/response fields. Keep the UI's area, crop, and season context aligned with the IDs and filters returned by the API; display missing evidence as unavailable rather than substituting mock values.

## Frontend integration notes

1. Configure the frontend API base URL to the backend URL for the current environment. Confirm `/health` and `/docs` load before diagnosing page-level failures.
2. Use `GET /segmentation/zones/page` and `GET /segmentation/agri-metrics/page` for tables. Preserve the returned pagination metadata and filters rather than loading an unbounded list.
3. For decision-making, get available crops/evidence from `/decision`; treat the returned historical NISR comparison as district-level evidence, not a farm forecast or causal claim.
4. For planning, send the selected zone and actual user-entered quantities to `/planification`; label estimates and unavailable input data clearly. Do not display guessed/default costs as verified local prices.
5. For community-authenticated routes, retain and send the community login token as the API specifies. Admin routes use the admin authentication flow. Avoid storing credentials or API secrets in frontend code.
6. The WhatsApp UI should report the backend's current mode/status. `WHATSAPP_MODE=mock` does not send real messages. Live mode needs server-side Meta credentials, webhook configuration, approved templates where required, and recorded recipient opt-in.

## Configuration and rollout status

- Backend variable names and safe defaults are documented in [`../.env.example`](../.env.example). Never commit a populated `.env` or expose Meta/Groq/JWT secrets to the browser.
- Migrations, model data, and runtime configuration are included in this branch; deployment still needs the target environment's database migration run and secrets configured.
- This is a code handoff, not a claim that the remote deployment or every route has been smoke-tested. Validate the API and migrations in the target environment before relying on live data or sending messages.

## Branch scope

This branch changes files under `backend/` plus this note. Frontend files are intentionally left for the frontend owner to reconcile and integrate against these API contracts. The existing feature PR remains separate and may still show conflicts.
