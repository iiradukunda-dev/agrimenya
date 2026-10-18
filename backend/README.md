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

WhatsApp Cloud API support is being added as an offline-first feature. The
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

Yield predictions use the latest validated NISR observations stored in
Supabase. The serving path does not read the bundled baseline CSV or JSON.
`GET /decision/model-info` identifies the database baseline and reports the
separate offline evaluation record. Until model features and validation use
the versioned database releases too, trained candidates are not served.

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

The runtime image needs the interval calibration artifact and database access;
training tables and baseline-generation files stay in the offline retraining
workflow. Readiness returns unavailable if the database has no yield evidence.

Apply migrations `0001` through `0009` in order to Supabase before deploying
this version. They add field reports, unknown prediction priority, readiness
and work records, WhatsApp consent and delivery, alert approval, versioned NISR
releases, named administrator accounts with hashed password recovery tokens,
and an individually authenticated farmer discussion board. The community is a
pilot: roles and email addresses are not verified and account recovery is not
available yet.

The Rwanda Space Agency's public orthomosaic map layer is optional visual
context, not a numeric input to yield predictions or priority rankings. See
[`docs/satellite_and_community.md`](docs/satellite_and_community.md) before
using either feature beyond development.

Resource quantities are calculated only from rates and prices supplied by the
user; the service does not prescribe application rates. Finance, nutrition,
climate-risk, export-approval, and jobs-supported scores remain unavailable
without validated methods and evidence. Evidence checklists and observed
worker-day records are descriptive inputs, not those scores. Weather requests
return unavailable on an unknown district or provider failure; they do not
substitute a fixed snapshot.
Symptom-only disease inputs return unconfirmed, and image-model scores are
labelled uncalibrated. These changes remove heuristic figures that could be
mistaken for measured results.
