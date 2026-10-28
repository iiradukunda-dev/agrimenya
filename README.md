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

### Option A: Run from the repository root (recommended)

Running Compose from the root starts both the FastAPI backend on port 8000
and the Streamlit frontend on port 8501. The frontend automatically connects
to the backend using the internal Docker network (`http://backend:8000`).

```powershell
Copy-Item backend\.env.example backend\.env
# Edit backend/.env and set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY
docker compose up --build
```

### Option B: Run from the backend directory

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

View running containers and logs:

```powershell
docker compose ps
docker compose logs -f
```

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
order, `0001` through `0016`, using the Supabase SQL editor or migration runner.

- `0001` to `0004`: Baseline zones, predictions, roadmaps, and alerts schema.
- `0005` and `0006`: WhatsApp contacts, message tracking, consent, and alert approval.
- `0007`: Versioned NISR yield imports and activation.
- `0008`: Named administrator accounts and secure password recovery tokens.
- `0009`: Authenticated farmer discussions and moderation reports.
- `0010`: Dated farmer field observations with optional private photos.
- `0011`: Unique lowercase community usernames.`n- `0014`: Saved plan action status history.`n- `0015`: Community email verification and shared rate limits.`n- `0016`: Optional Google sign-in for Community accounts.

Observations stay separate from official NISR yield records and are never
used as NISR baselines. Check the migration comments and `backend/docs/`
before applying these changes to production.

After startup, check `http://localhost:8000/health`. For prediction readiness,
the database needs yield observations; the health endpoint reports whether
they are present.

## Administrator access and recovery

Apply migration `0008_admin_accounts.sql` and configure SMTP in
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
observations rather than bundled CSV files. Import history and the format are
documented in `backend/docs/nisr_imports_and_access.md`.

Training and evaluation are offline workflows. They may use source datasets
that are intentionally excluded from the runtime Docker image. See
`backend/docs/retraining.md` before creating training artifacts.

## Users, WhatsApp, and production readiness

The frontend presents role-oriented views for citizens/farmers, planners,
cooperative leaders, and administrators. Administrator access uses named
accounts. Complete server-enforced ownership scopes are documented in
`backend/docs/nisr_imports_and_access.md`.

The farmer discussion pilot supports posts, comments, abuse reports, and
administrator moderation. Accounts and roles are currently self-reported. The
Rwanda Space Agency orthomosaic is an optional visual map layer only, not a
signal used to predict yield or prioritize zones. See
`backend/docs/satellite_and_community.md` for data limitations.

WhatsApp starts in mock mode. Live messaging requires Meta Cloud API
credentials, verified webhooks, opt-in records, and approved templates. Keep
all provider credentials in the backend environment. Configure production
secrets, HTTPS origins, allowed hostnames, email recovery, and operational
backups as described in `backend/docs/production_deployment.md`.

## Offline and PWA support

Agri-Menya includes a Progressive Web App service worker located in
`frontend/static/sw.js` and an offline fallback hub at
`frontend/static/offline.html`. When field workers navigate remote zones with
unstable network coverage, cached crop guides, offline field notes, and
emergency agronomy procedures remain accessible without an active connection.

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
│   ├── maps.py              # Interactive Folium map with Rwanda district centroids
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
