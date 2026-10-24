# Production deployment

## Required secrets and origins

Create the backend `.env` from `.env.example` in the deployment environment. Do not commit or copy a real `.env` into a container image.

Set these values before starting with `APP_ENV=production`:

- `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`: use the project's server-side secret key. The current local configuration uses a publishable key, which is suitable for reads when RLS allows them but not for production server-side writes.
- `USER_API_KEY`: a random value of at least 32 characters for protected user write APIs. Administrator access uses named accounts and short-lived bearer sessions; the legacy `ADMIN_API_KEY` is no longer accepted.
- `JWT_SECRET`: a separate random value of at least 32 characters.
- `SMTP_HOST`, `EMAIL_FROM`, optional `SMTP_USER`/`SMTP_PASSWORD`, TLS settings, `ADMIN_PASSWORD_RESET_URL`, and `COMMUNITY_PASSWORD_RESET_URL`: backend-only mail settings for administrator and farmer-community recovery, community email verification, invitations, and administrator-issued alert broadcasts. A newly sent alert is emailed to every active Farmer Community account; keep SMTP credentials backend-only. URLs must be HTTPS and point to the corresponding frontend pages.
- `ALLOWED_ORIGINS`: exact allowed browser origins, including scheme and port.
- `ALLOWED_HOSTS`: exact API hostnames accepted by the service. Include the service hostname and `127.0.0.1` for the container health probe.
- `GROQ_API_KEY` and `LLM_PROVIDER=groq`: configure the optional Groq chat provider on the backend only. The default model is `openai/gpt-oss-20b`; the grounded local responder remains active if the key is absent or the API is unavailable. Do not expose the provider key to Streamlit or the browser.
- `GROQ_VISION_MODEL`: optional Groq vision-capable model for preliminary crop-photo triage. Photos are resized/re-encoded in memory and sent to Groq; this endpoint does not retain them. Results are unconfirmed and must be checked by an agronomist before treatment.
- `WHATSAPP_MODE=mock` is the safe default. For live WhatsApp, use `WHATSAPP_MODE=live` with the Meta Cloud API `WHATSAPP_GRAPH_VERSION`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_BUSINESS_ACCOUNT_ID`, `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_APP_SECRET`, and `WHATSAPP_VERIFY_TOKEN`. Configure these backend-only secrets in the Meta environment; do not use Twilio WhatsApp credentials for this path.
- `WHATSAPP_PUBLIC_CHAT_ENABLED=false` keeps the Community click-to-chat link hidden even if credentials exist. Set it to `true` only after sender approval, public HTTPS webhook verification/delivery tests, approved templates, and an opted-in end-to-end test have all passed.

Generate separate values for every environment. Never place a Supabase service-role key in the frontend environment.

## Start and verify

From this directory, run:

```powershell
docker compose up --build -d
docker compose ps
Invoke-RestMethod https://<api-host>/health
```

The health response should report `status: ok` and `database_status: ok`. API documentation, OpenAPI, and the debug log route are disabled in production. Route writes and AI operations require the user key; admin routes require a named administrator session.

## Operational notes

- The container runs as a non-root user, has a health check, and excludes `.env`, logs, tests, and local data from its build context.
- Yield estimates use NISR observations in Supabase. Apply migration `0007_nisr_imports.sql` to enable release imports; check `baselines_present` and `yield_source` in health before accepting predictions. CSV training data is not required in the runtime image.
- SMS continues to use Twilio. WhatsApp is disabled in the legacy notification route and must use the contact-consent, alert-approval, template, and delivery-webhook path; API acceptance is not delivery confirmation. Apply the WhatsApp SQL migrations and obtain Meta template approval before production sends. The contact form requires `SMTP_HOST`, `EMAIL_FROM`, and `DEFAULT_NOTIFICATION_EMAIL`; outbound alert email also requires SMTP configuration. External LLM responses require `GROQ_API_KEY` when `LLM_PROVIDER=groq`, or `LLM_API_KEY` when explicitly using `LLM_PROVIDER=anthropic`. Verify the chosen provider in staging before enabling production delivery.
- Put the API behind an HTTPS reverse proxy and set `ALLOWED_HOSTS` to the externally visible API host.
- Back up Supabase data and validate RLS policies before deploying schema or credential changes.
- Before launch, run migrations through `0015`, verify service-role execution and RLS behavior in staging, test verification/reset mail to a controlled inbox, confirm an HTTPS browser/API flow, and record a successful Supabase backup plus restore drill. `/health` cannot prove backups, DNS, SMTP delivery, or Meta approval.
- Apply `app/db/migrations/0008_admin_accounts.sql` and `0009_farmer_community.sql` using the Supabase SQL editor or deployment migration runner. Provision the first administrator from a trusted backend host with `cd backend` then `python scripts/create_admin.py`; the script prompts for the password without echoing it. After that, use Admin → Access Management to invite or disable accounts. Lost administrator passwords are recovered through a 30-minute, single-use email link; reset increments the account session version and invalidates existing sessions. Administrator routes use named accounts; do not configure or rely on a shared `ADMIN_API_KEY`.
- Community registration requires a one-time email verification link, expires after 24 hours, and sign-in is denied until verified. Existing accounts must request a verification email after migration `0015`; confirm mail delivery before applying it to a live community. Password recovery uses a 30-minute, single-use email link. Community throttles use Supabase-backed shared fixed windows across API workers; retain edge-level controls as a second boundary. Roles remain self-reported and need independent verification for any privileged service. Publish community standards/privacy notices before public launch. Satellite imagery is not currently shown because the reviewed public mosaic had limited, undated coverage. See `satellite_and_community.md`.
- Authentication currently uses short-lived bearer tokens held in Streamlit server session state. Secure persistent `HttpOnly` cookie sign-in is not implemented: the browser talks to Streamlit while Streamlit makes server-side API requests, so API cookies would not automatically accompany those requests. Do not extend token lifetime or persist bearer tokens in browser storage as a workaround. Persistent sign-in requires an intentional same-origin session/BFF design with CSRF protection and a deployment proxy.
- Live WhatsApp stays unavailable until the business sender is approved, webhook verification and delivery callbacks work over public HTTPS, approved templates are configured, and an opt-in test is confirmed end to end. Keep `WHATSAPP_MODE=mock` until those external checks are complete.
- If the recovery mailbox is unavailable, an operator with trusted shell access and server-side database credentials can run `python scripts/reset_admin_password.py admin@example.org`; it also revokes existing sessions. Apply rate limits for `/auth/admin/*` at the HTTPS proxy as well, because the API's emergency local throttle is per process.
