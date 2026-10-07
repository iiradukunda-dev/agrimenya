# Production deployment

## Required secrets and origins

Create the backend `.env` from `.env.example` in the deployment environment. Do not commit or copy a real `.env` into a container image.

Set these values before starting with `APP_ENV=production`:

- `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`: use the project's server-side secret key. The current local configuration uses a publishable key, which is suitable for reads when RLS allows them but not for production server-side writes.
- `ADMIN_API_KEY` and `USER_API_KEY`: separate random credentials, each at least 32 characters. Keep them in the Streamlit server environment and send them as `X-Admin-Key` and `X-API-Key` respectively.
- `JWT_SECRET`: a separate random value of at least 32 characters.
- `ALLOWED_ORIGINS`: exact allowed browser origins, including scheme and port.
- `ALLOWED_HOSTS`: exact API hostnames accepted by the service. Include the service hostname and `127.0.0.1` for the container health probe.

Generate separate values for every environment. Never place a Supabase service-role key in the frontend environment.

## Start and verify

From this directory, run:

```powershell
docker compose up --build -d
docker compose ps
Invoke-RestMethod https://<api-host>/health
```

The health response should report `status: ok` and `database_status: ok`. API documentation, OpenAPI, and the debug log route are disabled in production. Route writes and AI operations require the user key; admin routes require the admin key.

## Operational notes

- The container runs as a non-root user, has a health check, and excludes `.env`, logs, tests, and local data from its build context.
- Trained files under `app/ml/artifacts` are packaged with the service. Check `model_present` and `baselines_present` in health before accepting yield predictions.
- SMS and WhatsApp notifications remain queued unless Twilio credentials are configured. The contact form requires `SMTP_HOST`, `EMAIL_FROM`, and `DEFAULT_NOTIFICATION_EMAIL`; outbound alert email also requires SMTP configuration. External LLM responses require `LLM_API_KEY`. Verify each provider in staging before enabling production delivery.
- Put the API behind an HTTPS reverse proxy and set `ALLOWED_HOSTS` to the externally visible API host.
- Back up Supabase data and validate RLS policies before deploying schema or credential changes.
