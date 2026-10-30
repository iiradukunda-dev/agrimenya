# Backend handoff for frontend integration

This note summarizes the API contracts available in this repository. The
running API's OpenAPI document at `/docs` is the source of truth for request
and response fields.

## API groups

| Purpose | Prefix | Examples |
| --- | --- | --- |
| Decision evidence | `/decision` | Crops, evidence ranking, district ranking, predictions, recommendations |
| Segmentation and retrieval | `/segmentation` | Districts, paginated zones and agricultural metrics, zone summaries, crop comparisons |
| Planning | `/planification` | Zone resources, roadmaps, saved plans |
| Assistant and crop health | `/chat` | Assistant, disease triage, uploaded-photo triage |
| Community | `/community` | Accounts, posts, comments, field reports, moderation |
| Communication and WhatsApp | `/communication`, `/webhooks` | Contacts, alerts, WhatsApp status, consent, delivery, webhook |
| Administration | `/auth/admin`, `/admin` | Admin authentication and protected operational routes |
| Live data | `/live-data` | Live-data and freshness status |

Use the route schemas in `/docs` to confirm exact names, parameters, and fields.
Use paginated endpoints for large zone and metric collections, and preserve
their pagination metadata and filters. Keep area, crop, and season context
aligned with API IDs and filters.

## Data and evidence handling

- Display missing values as unavailable; do not substitute guessed or mock
  values as verified observations.
- NISR yield comparisons are historical district-level evidence, not farm
  forecasts or causal claims.
- Planning estimates depend on user-provided quantities. Label estimates and
  unavailable costs clearly.
- Satellite imagery is visual context only; it is not field-level crop,
  condition, or suitability evidence. See
  [satellite and community notes](./satellite_and_community.md).

## Authentication and communication

- Community routes use the community token and session rules documented by
  the API. Admin routes use the separate admin authentication flow.
- Never store backend credentials in frontend code or expose them to the
  browser.
- The default WhatsApp mode is `mock` and does not send messages. Live delivery
  requires backend-only Meta credentials, webhook configuration, approved
  templates where required, and recipient opt-in.
- Google Community OAuth configuration and same-origin Render behavior are
  documented in [production deployment](./production_deployment.md).

## Deployment and migrations

The deployment configuration and required environment variables are documented
in [production deployment](./production_deployment.md). Apply only migrations
that are not already recorded by the target database, in numeric order through
the latest migration present in `backend/app/db/migrations/`; do not rerun
schema changes against an already-migrated database. A code handoff is not
confirmation that the deployed API, database migrations, or every route has
been smoke-tested.
