# agrimenya

agrimenya is a Rwanda-focused agricultural decision and planning support
system. The Streamlit frontend calls a FastAPI backend, which reads and writes
application data in Supabase. Yield estimates use validated NISR observations
stored in the database. WhatsApp is an optional access and notification
channel; mock mode is the default until Meta credentials and approved message
templates are configured.

## Project layout

- `frontend/`: Streamlit application for farmers, planners, cooperative
  leaders, and administrators.
- `frontend/static/`: PWA service worker, web manifest, and offline hub for
  field extension workers in low-connectivity areas.
- `backend/app/`: FastAPI routes, services, database access, and yield logic.
- `backend/app/db/migrations/`: ordered SQL migrations for the Supabase
  schema.
- `backend/scripts/`: administrator provisioning, NISR data preparation, and
  offline evaluation tools.
- `backend/docs/`: deployment, data import, retraining, model, and WhatsApp
  operating notes.
- `data/` — submission notes pointing to the project datasets in `backend/data/`.
- `demo/` — instructions for the short product walkthrough recording.
- `student_cards/` — instructions for handling official eligibility documents;
  personal documents should be submitted through an approved private channel.

## Project submission materials

Agri-Menya communicates district- and crop-level agricultural evidence,
including NISR yield observations and seasonal context, to help users explore
zones, compare crop information, review recommendations, and plan field
activities. Users navigate the Streamlit interface, select a district or crop,
inspect maps and evidence, and use the available planning and field-reporting
workflows. The floating bulb opens the AI assistant for agricultural questions
and decision support. The live application uses a Streamlit frontend, a FastAPI
backend, and Supabase for application records; see
[`backend/docs/frontend_backend_handoff.md`](backend/docs/frontend_backend_handoff.md)
for the API integration details.
If the API is unavailable, the AI Assistant can still show historical NISR
district-yield context from the bundled dataset. This offline fallback is not an
AI-generated answer, disease diagnosis, or zone-specific action; those require
the live API.

The repository already includes the README, application scripts, and project
datasets. Data inventory and source notes are in [`data/README.md`](data/README.md).
The live application is available at
<https://agrimenya-app-20261030.onrender.com/>. The product walkthrough is
[shared on Google Drive](https://drive.google.com/file/d/17Ko3W0DCiL7RJbVDtnvmJQp4RtiH60uL/view).
Set the Drive file's General access to "Anyone with the link" so reviewers can
open it. The frontend's `frontend/assets/landing video.mp4` is a site asset,
not the product demonstration.

Reviewer administrator credentials are not published in this repository.
Provide the account email and password only through an organizer-approved
private channel, and use a dedicated demo account rather than production
administrator credentials.

Dependencies are separated by service: install
[`backend/requirements.txt`](backend/requirements.txt) for the API or
[`frontend/requirements.txt`](frontend/requirements.txt) for the Streamlit app.
See the local development section below to set up both services.

Eligibility documents are personal records. The `student_cards/` folder is
intentionally a safe placeholder; do not commit student cards or identity
documents to this public repository. Submit the minimum official evidence
through the organizers' approved private channel. If the organizers explicitly
require repository submission, first confirm an approved restricted repository
and handling procedure.

## Requirements

- Python 3.12 for Docker images (Python 3.11 or newer for local development).
- Docker Desktop with Docker Compose, or separate Python environments for
  local development.
- A Supabase project with migrations applied. The backend needs the project
  URL and service role key appropriate to the environment.

## Timezone

The system default timezone is strictly Central Africa Time (CAT) UTC+2
(`Africa/Kigali`). All backend operations, observation timestamps, weather
forecasts, and user-facing dates reflect CAT.

## Git workflow and branch policy

The active development branch is `develop`.

- Always branch from and merge into `develop`.
- Do not push directly to `main` without explicit instruction.
- Never commit `.env` files, API credentials, passwords, or local logs.

```powershell
git clone --branch develop https://github.com/iiradukunda-dev/agrimenya.git
cd agrimenya
```

## Running with Docker Compose

Create `backend/.env` from `backend/.env.example` and set at minimum the
Supabase settings (`SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`).
To see the same live records as another team, both teams need access to the
same Supabase project; exchange credentials through an approved secure channel,
never by committing `.env` to GitHub. Apply migrations `0001` through `0018` if
they are not already applied. Set `JWT_SECRET` to a private random value of at
least 32 characters for community sessions.

For interactive Google satellite maps, create a root `.env` from `.env.example`
and set `GOOGLE_MAPS_API_KEY`. Restrict this browser key to the Maps JavaScript
API and the application's allowed HTTP referrers; enable billing in Google
Cloud. Map boundaries load from NISR census mapping as you zoom from districts
to sectors, cells, and villages. Never commit the populated `.env` file.

### Option A: Run from the repository root (recommended)

Running Compose from the root starts the FastAPI backend on port 8000 and the
Streamlit frontend behind a same-origin Nginx PWA gateway on port 8501. The
gateway serves the root-scoped manifest, service worker, and offline hub, and
passes Streamlit HTTP and WebSocket traffic through. The frontend connects to
the backend using the internal Docker network (`http://backend:8000`).

```powershell
Copy-Item .env.example .env
# Edit .env and set GOOGLE_MAPS_API_KEY
Copy-Item backend\.env.example backend\.env
# Edit backend/.env and set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY
docker compose up --build
```

Open the app at `http://localhost:8501` and the API health page at
`http://localhost:8000/health`. The shared branch runs WhatsApp in mock mode;
live WhatsApp and AI-provider behavior require their own backend credentials.
The setup and local development instructions below cover non-Docker options.

For a populated, isolated synthetic environment to explore the product, use
[`backend/docs/interactive_demo_data.md`](backend/docs/interactive_demo_data.md).
The demo seed is guarded, repeatable, and must only target a separate demo
Supabase project.

Never commit `.env` files, service-role keys, WhatsApp/email/LLM credentials,
passwords, or local logs. The backend service-role key must stay in the
backend environment; do not copy it to Streamlit or the browser.

You can also run Compose directly from `backend/`:

```powershell
cd backend
Copy-Item .env.example .env
# Edit .env with Supabase credentials
docker compose up --build
```

Once running, access:
- Streamlit application: `http://localhost:8501`
- FastAPI health check: `http://localhost:8000/health`
- FastAPI OpenAPI documentation: `http://localhost:8000/docs`

Stop the containers with `Ctrl+C` or by running:

```powershell
docker compose down
```

### Production Docker deployment

Production uses a separate Compose stack with Caddy-managed HTTPS. From the
repository root, copy `backend/production.env.example` to
`backend/.env.production`, replace the example domains and secret placeholders,
point both DNS names at the Docker host, and ensure public ports 80 and 443 are
available. Then run:

```powershell
cd backend
docker compose --env-file .env.production -f docker-compose.production.yml config
docker compose --env-file .env.production -f docker-compose.production.yml up --build -d
docker compose --env-file .env.production -f docker-compose.production.yml ps
```

Only the HTTPS proxy publishes host ports; the API and frontend remain on the
private Compose network. See
[`backend/docs/production_deployment.md`](backend/docs/production_deployment.md)
for required secrets, Google OAuth setup, migrations, staging checks, and
remaining external-service launch gates. Do not deploy with the example
environment values.

Set `FRONTEND_PORT` in the Compose environment to change the host port. The
frontend image excludes local environments, secrets, logs, and editor files;
the backend build also excludes `.env` and offline datasets. Compose requires
the backend `.env` file to exist before startup.

### Render Free-tier health checks and keep-alive

The backend exposes a fast, database-independent `GET /health` liveness check,
`GET /health/status` for the Admin dashboard's detailed database and baseline
status, and `GET /health/deep` for a bounded PostgreSQL `SELECT 1`. Configure
the backend-only `SUPABASE_DB_URL` secret in Render with the Supabase PostgreSQL
connection string; it is used only by the deep check and is not included in
health responses.

The GitHub Actions workflow at
[`keep-alive.yml`](.github/workflows/keep-alive.yml) checks the API every ten
minutes. After six failed liveness attempts it calls Render's service restart
API, then checks health again. A separate daily run checks `/health/deep`.
GitHub Actions secrets required by the workflow:

- `BACKEND_URL`: backend base URL, such as `https://agrimenya-api-20261030.onrender.com`.
- `RENDER_API_KEY`: a Render API key with permission to restart the backend service.
- `RENDER_SERVICE_ID`: the backend service ID shown in its Render dashboard.

The schedule runs only when this workflow is on the repository's default
branch. Use **Actions → Render API keep-alive → Run workflow** to test it
manually, or merge the workflow to the default branch to enable the schedule.
Never put these credentials in the workflow file or repository variables.

**This is a best-effort workaround, not an always-on guarantee.** Render Free
services can sleep after 15 minutes without inbound traffic, restart at any
time, and have a shared 750 free instance-hours/month workspace allowance.
Pinging the API every ten minutes keeps that service active and can consume
roughly 720 instance-hours/month by itself; the frontend is a separate Free
service and can still sleep. Scheduled jobs can be delayed or missed, and
Render can suspend services when the monthly allowance is exhausted. This
workflow cannot guarantee uninterrupted service. Render Starter or higher is
needed to avoid Free-tier idle spin-down; it does not prevent every possible
outage or restart.

For a new Blueprint deployment, Render prompts for environment values marked
`sync: false` in [`render.yaml`](render.yaml). Enter credentials in Render
only; generated `USER_API_KEY` and `JWT_SECRET` values are managed by Render.

## Local development without Docker

Create `backend/.env` from `backend/.env.example`, then set `SUPABASE_URL` and
`SUPABASE_KEY` (or `SUPABASE_SERVICE_ROLE_KEY`). The publishable key supports
only operations allowed by the database RLS policies; server-side writes need
the service-role key. Never place the service-role key in the frontend.

In PowerShell terminal 1, install and start the API:

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In PowerShell terminal 2, install and start Streamlit:

```powershell
cd frontend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
streamlit run Home.py --server.port 8501
```

The frontend `.env` defaults to `API_BASE_URL=http://localhost:8000`. Set its
`USER_API_KEY` to the same value as the backend when using protected user
operations. Restart the relevant service after changing environment values.

## Database setup

Apply the SQL files in `backend/app/db/migrations/` to Supabase in numeric
order, `0001` through `0018`, using the Supabase SQL editor or your migration
runner. Migrations `0005` and `0006` add WhatsApp contacts, message tracking,
consent, and alert approval; `0007` enables versioned NISR yield imports; and
`0008` adds named administrator accounts and password recovery tokens; `0009`
adds individually authenticated farmer discussions and moderation reports; `0010`
adds dated farmer field observations with optional private, compressed photos;
`0011` enforces unique lowercase community usernames.
`0014` adds action status history for saved plans. `0015` adds one-time
community email verification and shared API rate-limit storage. Existing
community accounts need to verify their email through the resend flow after
`0015` is applied. `0016` enables optional Google sign-in for Community.
`0017` adds named, separately mapped farm sites and optional farmer-drawn field outlines.
`0018` binds Google Community sign-in handoff codes to the browser that started
the OAuth flow.
Configure an email provider and the public Community URL before launch. Render
Free services block outbound SMTP ports, so use `EMAIL_PROVIDER=resend` with a
verified sending domain and a backend-only `RESEND_API_KEY`. Gmail SMTP requires
a paid Render service, `smtp.gmail.com` on port 587 with STARTTLS, matching
`EMAIL_FROM` and `SMTP_USER`, and a Google App Password (not the normal account
password).
These observations stay separate from official NISR yield records and are never
used as NISR baselines. Check
the migration comments and `backend/docs/` before applying these changes to a
production database.

After startup, check `http://localhost:8000/health` for API liveness and
`http://localhost:8000/health/status` for database and baseline details.
Prediction readiness depends on the available yield observations.

## Administrator access and recovery

Apply migration `0008_admin_accounts.sql` and configure email delivery in
`backend/.env`. For production, set `ADMIN_PASSWORD_RESET_URL` to the public
HTTPS Admin page. Bootstrap the first named administrator from a trusted
backend shell:

```powershell
cd backend
python scripts/create_admin.py
```

The script prompts for a password without displaying it. Password recovery
uses a single-use link that expires after 30 minutes. If the recovery mailbox
is unavailable, an operator with trusted shell and database access can reset
the account with:

```powershell
python scripts/reset_admin_password.py admin@example.org
```

This invalidates existing administrator sessions. See
`backend/docs/production_deployment.md` for production settings and
administrator operations.

## NISR yield data

Administrators can import a normalized NISR CSV after migration `0007` is
applied. Required columns are `district`, `crop`, `season`, and positive
`yield_kg_ha`; optional columns are `production_mt` and `cultivated_area_ha`.
Review each release source and mapped values before import. The server stages
and validates rows before activation; predictions read active database
observations rather than a few bundled CSV files. Import history and the full
format are documented in
[`backend/docs/nisr_imports_and_access.md`](backend/docs/nisr_imports_and_access.md).
The latest zone and yield provenance check, including limits on saved assessment
metadata and unverified coordinates, is recorded in
[`backend/docs/zone_data_provenance.md`](backend/docs/zone_data_provenance.md).

Training and evaluation are offline workflows. They may use source datasets
that are intentionally excluded from the runtime Docker image. See
`backend/docs/retraining.md` before creating training artifacts.

## Users, WhatsApp, and production readiness

The frontend presents role-oriented experiences for citizens/farmers,
planners, cooperative leaders, and administrators. Administrator access uses
named accounts. Individual citizen/planner/cooperative accounts and complete
server-enforced ownership or membership scopes are still required before
those experiences can be treated as production access control; see the access
model in `backend/docs/nisr_imports_and_access.md`.

The optional farmer discussion pilot supports posts, comments, abuse reports,
and administrator moderation. Email verification is required at sign-in, while
farmer/organization roles remain self-reported. Farmer password recovery uses
a single-use email link. Satellite imagery is
currently removed because the reviewed public mosaic had limited, undated
coverage and did not support dependable crop monitoring. See
[`backend/docs/satellite_and_community.md`](backend/docs/satellite_and_community.md)
for data limitations and safeguards.

WhatsApp starts in mock mode. Live messaging requires Meta Cloud API
credentials, verified webhooks, opt-in records, and approved templates. Keep
all provider credentials in the backend environment. Configure production
secrets, HTTPS origins, allowed hostnames, email recovery, and operational
backups as described in
[`backend/docs/production_deployment.md`](backend/docs/production_deployment.md).
For the Meta account, app, webhook, and test-to-live setup sequence, see
[`backend/docs/whatsapp_meta_cloud_api_setup.md`](backend/docs/whatsapp_meta_cloud_api_setup.md).

## Offline and PWA support

Agri-Menya includes a Progressive Web App service worker located in
`frontend/static/sw.js` and an offline fallback hub at
`frontend/static/offline.html`. Use the Docker Compose gateway on port 8501;
opening Streamlit directly on port 8501 bypasses the root-scoped worker routes.
Install from a secure HTTPS deployment (or `localhost` for local testing):

- Windows: use Install in Microsoft Edge or Chrome.
- Android: use Install app in Chrome.
- iPhone/iPad: in Safari, tap Share, then Add to Home Screen.

The worker caches the standalone offline hub, icons, and manifest. Offline field
notes saved in that hub remain on the device; live Streamlit dashboards and
backend-backed operations still require a network connection. public deployment
must terminate TLS at an HTTPS reverse proxy and forward traffic to the Compose
gateway while preserving the original `X-Forwarded-Proto` header. Test the
installed experience on physical iOS and Android devices before release.

## Validation and tests

### Backend test suite

Run the backend pytest suite from `backend/`:

```powershell
cd backend
python -m pytest tests -q
```

### Frontend test suite

Run the frontend test suite from the root directory:

```powershell
python -m pytest -o pythonpath=frontend frontend/utils/ -q
```

### Docker image builds

Verify that both Docker images build cleanly:

```powershell
docker compose build
```


## Frontend UI Architecture & Dashboard Widgets

The Agri-Menya frontend is structured around an executive, modular design system with responsive layouts and persistent theme support (Light & Dark modes).

### Directory Structure
```text
frontend/
├── Home.py                  # Entrypoint & operational pipeline overview
├── pages/                   # Multi-page routes (Dashboard, Zones, Planning, etc.)
├── views/                   # Core business views (views/dashboard.py, etc.)
├── components/              # Design system library:
│   ├── navbar.py            # Executive header, breadcrumbs, theme toggle, nav links
│   ├── cards.py             # KPI cards with SVG sparklines, forecast cards, empty states
│   ├── charts.py            # Responsive Plotly charts (bar, donut, area)
│   ├── badges.py            # Priority & status indicators with pulsing dots
│   ├── maps.py              # Interactive Google Maps satellite maps and Rwanda overlays
│   └── errors.py            # Error boundaries & sanitized failure screens
└── utils/
    ├── theme.py             # Dynamic CSS tokens, light/dark themes, card elevation
    ├── i18n.py              # Multi-lingual translations (EN, RW, FR)
    └── api_client.py        # Cached API client with offline mock fallbacks
```

### How to Add a New Dashboard Widget

To add a new dashboard metric, chart, or card to `frontend/views/dashboard.py`:

1. **Register the Data Fetcher (`frontend/utils/api_client.py`):**
   ```python
   @st.cache_data(ttl=300, show_spinner=False)
   def get_my_metric() -> dict[str, Any]:
       data = _get_api("/my-endpoint")
       return data if isinstance(data, dict) else {"count": 0}
   ```

2. **Create the Visual Component (`frontend/components/cards.py` or `charts.py`):**
   ```python
   def render_custom_widget(col, title: str, count: int, sparkline: list[float]):
       from components.cards import render_kpi_card
       render_kpi_card(
           col,
           title=title,
           value=count,
           sparkline_data=sparkline,
           delta=5.2,
           icon="""<svg ...>...</svg>"""
       )
   ```

3. **Mount in the Dashboard Grid (`frontend/views/dashboard.py`):**
   ```python
   # Inside render_dashboard():
   with st.container(border=True):
       render_custom_widget(col, "My Metric", data["count"], [10, 15, 20, 25])
   ```

4. **Add Localized Strings (`frontend/utils/i18n.py`):**
   Add keys under `FALLBACK_TRANSLATIONS` for `en`, `rw`, and `fr`.

### Full Backend-to-Frontend Feature Parity

Every backend service and endpoint is exposed through an interactive UI workflow:
- **Decision Engine (`/decision`):** Priority recommendations, field risk signal integration, agronomic disease risk evaluation, district yield gap benchmarking vs. national reference targets, Plotly comparison charts with CSV export, and ML model diagnostics & provenance display (XGBoost R²=0.83, MAE=214 kg/ha, split metrics, feature list, and known limitations).
- **Planification & Milestones (`/planification`):** Custom execution roadmaps, milestone action status updates (`planned`, `in_progress`, `completed`, `blocked`), milestone audit history trail, attached resource costing, one-click plan email dispatch via SMTP (`/communication/share/{plan_id}/send`), and rapid emergency disease response plan generator.
- **Communication Hub (`/communication`):** Real-time community alerts feed with severity filtering, broadcast field alert form with SMTP email distribution, multi-channel notification dispatch across SMS (Twilio), WhatsApp Cloud API, and Email, plus embedded WhatsApp contact registry and consent management.

## Copyright

© 2026 agrimenya. All rights reserved.
