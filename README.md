# Agri-Menya

Agri-Menya is a Rwanda-focused agricultural decision and planning support
system. The Streamlit frontend calls a FastAPI backend, which reads and writes
application data in Supabase. Yield estimates use validated NISR observations
stored in the database. WhatsApp is an optional access and notification
channel; mock mode is the default until Meta credentials and approved message
templates are configured.

## Project layout

- `frontend/` — Streamlit application for farmers, planners, cooperative
  leaders, and administrators.
- `backend/app/` — FastAPI routes, services, database access, and yield logic.
- `backend/app/db/migrations/` — ordered SQL migrations for the Supabase
  schema.
- `backend/scripts/` — administrator provisioning, NISR data preparation, and
  offline evaluation tools.
- `backend/docs/` — deployment, data import, retraining, model, and WhatsApp
  operating notes.

## Requirements

- Python 3.12 for the Docker images (Python 3.11 or newer for local
  development).
- Docker Desktop with Docker Compose, or separate Python environments for
  local development.
- A Supabase project with migrations applied. The backend needs the project
  URL and keys appropriate to the environment.

Never commit `.env` files, service-role keys, WhatsApp/SMTP/LLM credentials,
passwords, or local logs. The backend service-role key must stay in the
backend environment; do not copy it to Streamlit or the browser.

## Run both services with Docker Compose

Create `backend/.env` from the example and fill in at least the Supabase
settings. Run Compose from the `backend` directory so its `.env` file is used
for API settings and Compose variable interpolation:

```powershell
Copy-Item .env.example .env
# Edit .env and set the required Supabase values.
docker compose up --build
```

Open the frontend at `http://localhost:8501`; the API is available at
`http://localhost:8000`. Compose configures the frontend to call the API by its
internal service name. Stop the services with `Ctrl+C`, or run
`docker compose down` from `backend/`. View service status and logs with:

```powershell
docker compose ps
docker compose logs -f api frontend
```

Set `FRONTEND_PORT` in the Compose environment to change the host port. The
frontend image excludes local environments, secrets, logs, and editor files;
the backend build also excludes `.env` and offline datasets. Compose requires
the backend `.env` file to exist before startup.

## Local development without Docker

Create `backend/.env` from `backend/.env.example`, then set `SUPABASE_URL` and
`SUPABASE_KEY` (or `SUPABASE_SERVICE_ROLE_KEY`). The publishable key supports
only operations allowed by the database's RLS policies; server-side writes
need the service-role key. Do not put the service-role key in the frontend.

In PowerShell, install and run the API:

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal, install and run Streamlit:

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
order, `0001` through `0008`, using the Supabase SQL editor or your migration
runner. Migrations `0005` and `0006` add WhatsApp contacts, message tracking,
consent, and alert approval; `0007` enables versioned NISR yield imports; and
`0008` adds named administrator accounts and password recovery tokens. Check
the migration comments and `backend/docs/` before applying these changes to a
production database.

After startup, check `http://localhost:8000/health`. For prediction readiness,
the database needs yield observations; the health endpoint reports whether
they are present. A healthy API connection alone does not mean yield data is
available.

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

This invalidates existing administrator sessions. Do not configure the
service-role key in frontend settings. See
[`backend/docs/production_deployment.md`](backend/docs/production_deployment.md)
for production settings and administrator operations.

## NISR yield data

Administrators can import a normalized NISR CSV after migration `0007` is
applied. The required columns are `district`, `crop`, `season`, and positive
`yield_kg_ha`; optional columns are `production_mt` and `cultivated_area_ha`.
Review each release's source and mapped values before import. The server stages
and validates rows before activation; predictions read active database
observations rather than a few bundled CSV files. Import history and the full
format are documented in
[`backend/docs/nisr_imports_and_access.md`](backend/docs/nisr_imports_and_access.md).

Training and evaluation are offline workflows. They may use source datasets
that are intentionally excluded from the runtime Docker image and should be
handled according to their source and access terms. See
[`backend/docs/retraining.md`](backend/docs/retraining.md) before creating
training artifacts.

## Users, WhatsApp, and production readiness

The frontend presents role-oriented experiences for citizens/farmers,
planners, cooperative leaders, and administrators. Administrator access uses
named accounts. Individual citizen/planner/cooperative accounts and complete
server-enforced ownership or membership scopes are still required before
those experiences can be treated as production access control; see the access
model in `backend/docs/nisr_imports_and_access.md`.

WhatsApp starts in mock mode. Live messaging requires Meta Cloud API
credentials, verified webhooks, opt-in records, and approved templates. Keep
all provider credentials in the backend environment. Configure production
secrets, HTTPS origins, allowed hostnames, email recovery, and operational
backups as described in
[`backend/docs/production_deployment.md`](backend/docs/production_deployment.md).

## Validation

Run the backend suite from `backend/` after installing its requirements:

```powershell
python -m pytest tests -q
```

Docker image builds can be checked from `backend/` with:

```powershell
docker compose build
```
