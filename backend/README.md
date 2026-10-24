# Agri-Menya backend

For repository-wide setup instructions covering both FastAPI and Streamlit,
Docker Compose, migrations, and deployment, see the [project README](../README.md).

## Administrator access

Admin tools use named accounts rather than a shared key. Apply
`app/db/migrations/0008_admin_accounts.sql`, configure backend SMTP plus an
HTTPS `ADMIN_PASSWORD_RESET_URL`, then bootstrap the first account from a
trusted backend host with `python scripts/create_admin.py` (run from the
`backend` directory). Administrators can invite or disable accounts in the
Admin panel. Password recovery sends a one-time link that expires after 30
minutes; password changes revoke existing sessions. Do not expose reset tokens
or SMTP credentials in frontend configuration. If recovery email is unavailable,
an operator can reset an account from a trusted backend shell with
`python scripts/reset_admin_password.py admin@example.org`.

## WhatsApp notifications

WhatsApp Cloud API support is available as an offline-first feature. The
default `WHATSAPP_MODE=mock` sends only to an in-memory mock provider. Live mode
requires the Meta access token, app secret, verify token, graph version, and
phone number ID in the backend environment. Never configure these in
Streamlit. `GET /communication/whatsapp-status` returns safe readiness flags.
Recipient phone numbers use E.164 format, for example `+2507XXXXXXXX`.

The legacy Twilio SMS integration remains available. The legacy direct Twilio
WhatsApp send path is disabled; WhatsApp messages must use the consent and
approved-dispatch flow. API acceptance is not delivery confirmation; status
webhooks provide delivery state. Follow Meta's current rules for opt-in,
customer-service windows, approved utility templates, and pricing.
See [`docs/whatsapp_meta_cloud_api_setup.md`](docs/whatsapp_meta_cloud_api_setup.md)
for Meta Business setup, backend environment mapping, webhook configuration,
and the test-to-live checklist. Template names and parameters are documented in
[`docs/whatsapp_templates.md`](docs/whatsapp_templates.md).

## AI assistant provider

The assistant defaults to Groq (`LLM_PROVIDER=groq`) using
`openai/gpt-oss-20b`. Create an API key in the GroqCloud console and set
`GROQ_API_KEY` in the backend's local `.env`; never put it in Streamlit or
commit it. The backend sends only the selected district DATA block and the
bounded chat history. Every model answer still passes the server-side number,
source, and scope checks; rejected or unavailable responses use the grounded
local responder. Without a Groq key, the local responder remains available.

Groq's free plan has organization-level request/token limits, so expect
fallback responses if those limits are reached. Groq says inference inputs and
outputs are not retained by default, with limited temporary retention for
reliability/abuse investigations. Review Groq's current data policy before
using non-public or personal information. The free Gemini API is not selected
because Google states that unpaid-tier prompts and responses can be used to
improve products.

## Yield baseline and offline model work

Yield predictions prefer validated NISR observations stored in Supabase and
fill missing district/crop/season coverage from the bundled official SAS
tables for 2022–2026. The versioned source is
`data/nisr_official_yields_2022_2026.csv`; it contains overall district tables
only, with farmer reports and SITE subgroup estimates excluded. Database rows
supersede a bundled row for the same district, crop, and season. If an exact
year is unavailable, the baseline can pool the same season from available
years; prediction responses identify the source, period, and scope.
`GET /decision/model-info` reports the bundled source coverage. To rebuild the
CSV and its SHA-256 coverage report from the supplied official workbooks, run:

```powershell
python scripts/build_official_sas_baseline.py `
  --sas-2022 "C:\path\SAS 2022_Tables_0.xlsx" `
  --sas-2023 "C:\path\SAS 2023_Annual Tables.xlsx" `
  --sas-2024 "C:\path\SAS 2024_Annual Tables.xlsx" `
  --sas-2025 "C:\path\SAS 2025_Annual Tables.xlsx" `
  --sas-2026-a "C:\path\Tables_2026 Season A.xlsx" `
  --sas-2026-b "C:\path\Tables_2026 Season B.xlsx"
```

The active serving approach remains the validated observational baseline.
Trained candidates are not served until evaluation demonstrates that they
outperform it with the same versioned evidence and grouped validation.

Run the grouped model comparison from the backend directory:

```powershell
python -m app.ml.train_yield_model
```

This uses the fixed small candidate configurations and grouped district/season
validation. It writes evaluation and out-of-fold files under `data/eval/`. A
model pickle and model card are written only if the decision rule beats the
baseline on both split types. Current checked-in evaluation says `KEEP BASELINE`,
so deploys should report baseline mode. Do not commit `yield_model.pkl`; model
artifacts can be large and tied to a particular data and library version.

The runtime image includes the compact official SAS CSV fallback and interval
calibration. The app still requires database access for zones and other live
features; yield estimates can fall back to bundled official SAS data if the
database has no matching yield records.

Apply migrations `0001` through `0012` in order to Supabase before deploying
this version. They add field reports, unknown prediction priority, readiness
and work records, WhatsApp consent and delivery, alert approval, versioned NISR
releases, named administrator accounts with hashed password recovery tokens,
and an individually authenticated farmer discussion board. The community is a
pilot: roles and email addresses are not verified. Farmer password recovery
uses a 30-minute, single-use email link sent through configured SMTP.

Satellite imagery is not currently shown: the reviewed Rwanda Space Agency
public mosaic had limited, undated coverage and is not a reliable national
crop-monitoring layer. See
[`docs/satellite_and_community.md`](docs/satellite_and_community.md) before
using either feature beyond development.

Resource quantities are calculated only from rates and prices supplied by the
user; the service does not prescribe application rates. Finance, nutrition,
climate-risk, export-approval, and jobs-supported scores remain unavailable
without validated methods and evidence. Evidence checklists and observed
worker-day records are descriptive inputs, not those scores. Weather requests
return unavailable on an unknown district or provider failure; they do not
substitute a fixed snapshot.
Crop photos are sent to the configured Groq vision model for preliminary,
unconfirmed triage when available. The app does not display an uncalibrated
confidence score or treat the result as an agronomist's diagnosis.
