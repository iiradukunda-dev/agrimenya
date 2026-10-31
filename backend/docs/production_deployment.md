# Production deployment

## Required secrets and origins

Create `backend/.env.production` from `backend/production.env.example` on the deployment host. Do not commit or copy a real production environment file into a container image. Replace all example domains and secret placeholders. Use a DNS name for `APP_DOMAIN` and `API_DOMAIN` that resolves to the host running Docker; ports 80 and 443 must be reachable from the public internet so Caddy can issue and renew certificates. Google OAuth is reverse-proxied through `APP_DOMAIN`, so its callback and the Community page share one origin; leave `COMMUNITY_GOOGLE_HANDOFF_COOKIE_DOMAIN` unset.

Set these values before starting with `APP_ENV=production`:

- `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`: use the project's server-side secret key. The current local configuration uses a publishable key, which is suitable for reads when RLS allows them but not for production server-side writes.
- `USER_API_KEY`: a random value of at least 32 characters for protected user write APIs. Administrator access uses named accounts and short-lived bearer sessions; the legacy `ADMIN_API_KEY` is no longer accepted.
- `JWT_SECRET`: a separate random value of at least 32 characters.
- `EMAIL_PROVIDER`, `EMAIL_FROM`, `ADMIN_PASSWORD_RESET_URL`, and `COMMUNITY_PASSWORD_RESET_URL`: configure backend-only transactional email for administrator and farmer recovery, verification, invitations, contact messages, plan sharing, and alerts. On Render Free, use `EMAIL_PROVIDER=resend`, a backend-only `RESEND_API_KEY`, and `EMAIL_FROM` on a domain verified with Resend. The hosted `onrender.com` address and personal Gmail addresses are not domains you can verify for Resend. Render Free web services block outbound ports 25, 465, and 587, so SMTP cannot deliver from this deployment; use SMTP only after upgrading the backend service to a paid plan. For Gmail SMTP on a supported plan, use `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587`, `SMTP_STARTTLS=true`, `SMTP_USE_SSL=false`, `SMTP_USER` equal to the sending Gmail address, and `SMTP_PASSWORD` set to a Google App Password (not the normal account password); `EMAIL_FROM` must match that mailbox. Never put mail credentials in the frontend, chat, or source control. URLs must be HTTPS and point to the corresponding frontend pages.

For the Gmail sender on a paid Render instance, set these values in the **backend** Render service environment (never in chat or source control):

```text
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_STARTTLS=true
SMTP_USE_SSL=false
SMTP_USER=<the sending Gmail address>
SMTP_PASSWORD=<a Google App Password>
EMAIL_FROM=<the same sending Gmail address>
```

For the current Free Render deployment, configure `EMAIL_PROVIDER=resend`, a Resend API key, and a sender such as `no-reply@<your-verified-domain>` in the backend service. Add the DNS records Resend provides and wait for domain verification before sending. Save the variables and wait for redeploy; the Admin System Health tab reports configuration problems without revealing credentials. Then request a setup link from **Forgot password?** for the already-created administrator account.
- Optional Google Community sign-in: set backend-only `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, `GOOGLE_OAUTH_REDIRECT_URI`, and `COMMUNITY_GOOGLE_CALLBACK_URL`. Register the redirect URI exactly in Google Cloud Console. With Docker Compose or the Render configuration below, route the OAuth start and callback through the frontend hostname and use the Community page on that same hostname; leave the cookie domain unset. Apply migrations `0016` through `0018` in numeric order before enabling the updated API. Google-verified emails can create a farmer account; an existing account is automatically linked only when Google controls the email domain (Gmail or a matching Google Workspace hosted domain). Leave credentials unset to hide the Google button.
- `ALLOWED_ORIGINS`: exact allowed browser origins, including scheme and port.
- `ALLOWED_HOSTS`: exact API hostnames accepted by the service. Include the service hostname and `127.0.0.1` for the container health probe.
- `GROQ_API_KEY` and `LLM_PROVIDER=groq`: configure the optional Groq chat provider on the backend only. The default model is `openai/gpt-oss-20b`; the grounded local responder remains active if the key is absent or the API is unavailable. Do not expose the provider key to Streamlit or the browser.
- `GROQ_VISION_MODEL`: optional Groq vision-capable model for preliminary crop-photo triage. Photos are resized/re-encoded in memory and sent to Groq; this endpoint does not retain them. Results are unconfirmed and must be checked by an agronomist before treatment.
- `WHATSAPP_MODE=mock` is the safe default. For live WhatsApp, use `WHATSAPP_MODE=live` with the Meta Cloud API `WHATSAPP_GRAPH_VERSION`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_BUSINESS_ACCOUNT_ID`, `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_APP_SECRET`, and `WHATSAPP_VERIFY_TOKEN`. Configure these backend-only secrets in the Meta environment; do not use Twilio WhatsApp credentials for this path.
- `WHATSAPP_PUBLIC_CHAT_ENABLED=false` keeps the Community click-to-chat link hidden even if credentials exist. Set it to `true` only after sender approval, public HTTPS webhook verification/delivery tests, approved templates, and an opted-in end-to-end test have all passed.

Generate separate values for every environment. Never place a Supabase service-role key in the frontend environment.

## Render single-origin deployment (no custom domain)

The frontend Docker image includes Nginx. Regular API calls remain server-to-server
from Streamlit to FastAPI, and Nginx sends only the Google OAuth start and callback
paths to the API service. The browser uses the Streamlit hostname for the whole
login flow, keeping the short-lived HttpOnly handoff cookie on one origin without
requiring a custom domain or a cookie shared across `onrender.com` hostnames.

The root `render.yaml` defines two free Docker web services in Frankfurt. From
the Render Dashboard, choose **New > Blueprint**, connect this repository, and
select the deployment branch. The Blueprint declares the production environment
variable names and prompts for values marked `sync: false`, including the
backend-only Supabase and Resend credentials, sender identity, and optional
Google OAuth credentials. Enter credentials directly in Render; they are not
stored in `render.yaml`. Render generates separate `USER_API_KEY` and
`JWT_SECRET` values and securely references the user API key from the frontend
service. Set `SUPABASE_DB_URL` to the Supabase PostgreSQL connection string for
the daily deep database check.

Render's API web service uses the default `PORT=10000`; the API image listens on
Render's `PORT` and falls back to port 8000 for local Docker Compose.

The Blueprint uses the service names
`agrimenya-api-20261030` and `agrimenya-app-20261030`. Their expected public
URLs are used for CORS, recovery links, and Google callbacks. If Render reports
a hostname conflict and you change either service name, update the corresponding
hostnames in `render.yaml` before creating the Blueprint. Register this exact
Google redirect URI in Google Cloud Console:
`https://agrimenya-app-20261030.onrender.com/community/auth/google/callback`.
The Google Community callback is
`https://agrimenya-app-20261030.onrender.com/Community`.

Before enabling Google sign-in, apply migrations `0016` through `0018` to the
intended Supabase project. Verify account registration, Google sign-in, email
verification, password recovery, and Supabase writes after deployment. Keep
`WHATSAPP_MODE=mock` unless live Meta credentials and webhooks have been
configured and tested. The API service remains publicly addressable on its
Render URL, so retain its authentication and API-key protections.

The backend Render health check uses `GET /health`, a fast liveness endpoint
that does not depend on Supabase. `GET /health/status` retains the detailed
database and baseline information displayed in Admin. `GET /health/deep` runs
a bounded `SELECT 1` using `SUPABASE_DB_URL` and returns only a generic failure
body if PostgreSQL is unreachable.

The GitHub Actions workflow `.github/workflows/keep-alive.yml` pings `/health`
every ten minutes, requests a Render restart after six failed attempts, and
checks `/health/deep` daily. Configure the GitHub Actions secrets
`BACKEND_URL`, `RENDER_API_KEY`, and `RENDER_SERVICE_ID`. GitHub scheduled
workflows run from the repository's default branch; use workflow dispatch for
testing before merging there.

This is best-effort monitoring, not guaranteed uptime. Render Free services can
sleep after 15 idle minutes, restart at any time, and share a 750
instance-hours/month workspace allowance. Keeping the API warm can use about
720 hours/month, while the separate frontend may still sleep; delayed or missed
scheduled runs and exhausted free hours can still make the app unavailable.
Render Starter or higher avoids Free-tier idle spin-down, but does not prevent
every outage or restart.

## Start with the production Compose stack

The production stack is `docker-compose.production.yml`; it builds the existing
non-root API and Streamlit images and adds Caddy for automatic HTTPS. Only Caddy
publishes host ports. The API and frontend use internal Compose networking, and
the API is not directly exposed to the internet.

Before starting the stack, create DNS `A`/`AAAA` records for both
`APP_DOMAIN` and `API_DOMAIN`, allow inbound TCP ports 80 and 443 (and UDP 443
for HTTP/3) through the host firewall, and ensure no other service occupies
those ports. Caddy stores certificates in its named Docker volume; include
that volume in the host's protected backup plan.

From `backend/`, after configuring `.env.production`, run:

```text
Copy-Item production.env.example .env.production
# Generate two different values; store them in USER_API_KEY and JWT_SECRET.
python -c "import secrets; print(secrets.token_urlsafe(48))"
python -c "import secrets; print(secrets.token_urlsafe(48))"
docker compose --env-file .env.production -f docker-compose.production.yml config
docker compose --env-file .env.production -f docker-compose.production.yml up --build -d
docker compose --env-file .env.production -f docker-compose.production.yml ps
```

Use the API hostname for liveness, for example `https://api.example.org/health`, and confirm `status: alive`. Then check `https://api.example.org/health/status` for `database_status: ok`. Also open `https://app.example.org` in a browser and confirm the app loads. API documentation, OpenAPI, and the debug log route are disabled in production. Route writes and AI operations require the user key; admin routes require a named administrator session.

After startup, verify a controlled email-verification and password-reset
message reaches its recipient, complete a fresh Google sign-in if enabled,
confirm Supabase writes succeed with the service-role key and the intended RLS
policies, and exercise the core read-only decision and segmentation pages.
Keep WhatsApp in mock mode until Meta webhook verification, templates, opt-in,
and delivery callbacks have been tested end-to-end.

Run the one-time administrator bootstrap from a trusted backend host after
the API is configured, using the same production environment file:

```powershell
docker compose --env-file .env.production -f docker-compose.production.yml exec api python scripts/create_admin.py
```

This command prompts for the initial administrator details; do not put an
administrator password in the Compose file or environment template.

The production environment file is passed only to the API container. Compose
reads `USER_API_KEY` from that file and passes it to the Streamlit server for
server-to-server API requests; it is not embedded in the frontend image or sent
to the browser. The frontend never receives the Supabase service-role key or
provider credentials. Keep the environment file readable only by the
deployment operator. Back it up only through an approved encrypted
secret-management process.

For Google sign-in, register `https://<APP_DOMAIN>/community/auth/google/callback` as the exact authorized redirect URI in Google Cloud Console. Apply migrations through `0018` to the intended Supabase project before deploying the matching code. For a new database, apply all migrations in numeric order. After deployment, test sign-in in a fresh browser session.

## Operational notes

- The container runs as a non-root user, has a health check, and excludes `.env`, logs, tests, and local data from its build context.
- Yield estimates use NISR observations in Supabase. Apply migration `0007_nisr_imports.sql` to enable release imports; check `baselines_present` and `yield_source` in health before accepting predictions. CSV training data is not required in the runtime image.
- SMS continues to use Twilio. WhatsApp is disabled in the legacy notification route and must use the contact-consent, alert-approval, template, and delivery-webhook path; API acceptance is not delivery confirmation. Apply the WhatsApp SQL migrations and obtain Meta template approval before production sends. The contact form requires a configured email provider, `EMAIL_FROM`, and `DEFAULT_NOTIFICATION_EMAIL`; outbound alert email uses the same provider. External LLM responses require `GROQ_API_KEY` when `LLM_PROVIDER=groq`, or `LLM_API_KEY` when explicitly using `LLM_PROVIDER=anthropic`. Verify the chosen provider in staging before enabling production delivery.
- Put the API behind an HTTPS reverse proxy and set `ALLOWED_HOSTS` to the externally visible API host.
- Serve the frontend through the root Compose `pwa-gateway` on port 8501. Terminate public TLS at the ingress/reverse proxy and preserve `X-Forwarded-Proto: https` to the gateway. The gateway must serve `/sw.js`, `/manifest.json`, and `/offline.html` from the frontend static assets on the same origin; do not expose the Streamlit port directly for PWA use. iOS Add to Home Screen and Chromium install prompts require a secure public HTTPS origin.
- Back up Supabase data and validate RLS policies before deploying schema or credential changes.
- Before launch, run all applicable migrations through `0018`, verify service-role execution and RLS behavior in staging, test verification/reset mail to a controlled inbox, confirm an HTTPS browser/API flow, and record a successful Supabase backup plus restore drill. `/health` cannot prove backups, DNS, email delivery, or Meta approval.
- Apply `app/db/migrations/0008_admin_accounts.sql` and `0009_farmer_community.sql` using the Supabase SQL editor or deployment migration runner. Provision the first administrator from a trusted backend host with `cd backend` then `python scripts/create_admin.py`; the script prompts for the password without echoing it. After that, use Admin → Access Management to invite or disable accounts. Lost administrator passwords are recovered through a 30-minute, single-use email link; reset increments the account session version and invalidates existing sessions. Administrator routes use named accounts; do not configure or rely on a shared `ADMIN_API_KEY`.
- Community registration requires a one-time email verification link, expires after 24 hours, and sign-in is denied until verified. Existing accounts must request a verification email after migration `0015`; confirm mail delivery before applying it to a live community. Password recovery uses a 30-minute, single-use email link. Community throttles use Supabase-backed shared fixed windows across API workers; retain edge-level controls as a second boundary. Roles remain self-reported and need independent verification for any privileged service. Publish community standards/privacy notices before public launch. Satellite imagery is not currently shown because the reviewed public mosaic had limited, undated coverage. See `satellite_and_community.md`.
- Authentication currently uses short-lived bearer tokens held in Streamlit server session state. Secure persistent `HttpOnly` cookie sign-in is not implemented: the browser talks to Streamlit while Streamlit makes server-side API requests, so API cookies would not automatically accompany those requests. Do not extend token lifetime or persist bearer tokens in browser storage as a workaround. Persistent sign-in requires an intentional same-origin session/BFF design with CSRF protection and a deployment proxy.
- Live WhatsApp stays unavailable until the business sender is approved, webhook verification and delivery callbacks work over public HTTPS, approved templates are configured, and an opt-in test is confirmed end to end. Keep `WHATSAPP_MODE=mock` until those external checks are complete.
- If the recovery mailbox is unavailable, an operator with trusted shell access and server-side database credentials can run `python scripts/reset_admin_password.py admin@example.org`; it also revokes existing sessions. Apply rate limits for `/auth/admin/*` at the HTTPS proxy as well, because the API's emergency local throttle is per process.
