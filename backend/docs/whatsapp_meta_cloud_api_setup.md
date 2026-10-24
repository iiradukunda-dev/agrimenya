# Meta WhatsApp Cloud API setup

This guide connects Agri-Menya's existing WhatsApp integration to a WhatsApp
Business Account managed by Meta. It covers the Meta dashboard setup, backend
configuration, and a staged test-to-live rollout.

Agri-Menya already has a mock provider and a Meta Cloud API provider, inbound
message handling, webhook verification, consent and opt-out handling, message
delivery tracking, template-backed alert dispatch, and an English/Kinyarwanda
command bot. A WhatsApp product catalog is optional and is not needed for
these services.

## 1. Confirm the WhatsApp Business Account

In Meta Business Settings, open **Accounts > WhatsApp accounts** and select
the Agri-Menya account already created. Do not add another account if the
existing one is the intended sender. Assign the people who will manage it.

The phone-number information panel shown during setup had a **Pending** status.
Check the number and display-name status in WhatsApp Manager and complete any requested review,
verification, or registration steps before using that number for live
messaging. The developer app and Meta's test number can be set up while this
is pending.

Meta screens and labels can change. The [WhatsApp Business Developer
Hub](https://whatsappbusiness.com/developers/developer-hub/) links to the
current setup guide, API reference, webhook guidance, opt-in guidance, and
pricing information.

## 2. Create the Meta developer app

1. Open [Meta for Developers > My Apps](https://developers.facebook.com/apps/)
   and choose **Create App**.
2. Select the WhatsApp/business messaging use case offered in the current
   creation flow, and associate the app with the Agri-Menya business portfolio.
3. Add or open the **WhatsApp** product in the app dashboard.
4. Open **WhatsApp > API Setup**. Start with Meta's test number and add an
   authorized test recipient. Use the provided test access token and send the
   sample message to confirm that the test setup works.
5. Select the existing Agri-Menya WhatsApp Business Account and intended phone
   number when the setup flow offers account/number selection. Record the Phone
   Number ID and WhatsApp Business Account ID. These IDs are not access
   credentials, but keep them with the deployment configuration.

Do not paste access tokens or app secrets into chat, source code, tickets, or
screenshots. A dashboard test token is for testing; use a securely managed
production credential for a deployed integration, with the required WhatsApp
permissions and access to the correct business assets.

## 3. Configure the backend

All Cloud API settings belong in `backend/.env`, never the frontend `.env` or
browser configuration. The supported names are listed in
[`../.env.example`](../.env.example):

| Setting | Value |
| --- | --- |
| `WHATSAPP_MODE` | Keep `mock` during setup; change to `live` only for a deliberate live test. |
| `WHATSAPP_GRAPH_VERSION` | A Graph API version currently supported by Meta; pin the version used by the integration. |
| `WHATSAPP_PHONE_NUMBER_ID` | Phone Number ID shown by the WhatsApp API setup/account details. |
| `WHATSAPP_PUBLIC_NUMBER` | Ready, public Agri-Menya sender number in international `+` format; enables the Community click-to-chat link. This is not the Phone Number ID. |
| `WHATSAPP_BUSINESS_ACCOUNT_ID` | WhatsApp Business Account ID (WABA ID). |
| `WHATSAPP_ACCESS_TOKEN` | Secret access token authorized for the selected WhatsApp assets. |
| `WHATSAPP_APP_SECRET` | App secret from the Meta developer app settings; used to verify webhook signatures. |
| `WHATSAPP_VERIFY_TOKEN` | A private random string you choose and enter identically in Meta's webhook configuration. |
| `WHATSAPP_DAILY_CAP` | Agri-Menya's additional per-contact daily outbound limit. |

Keep the existing safe default `WHATSAPP_MODE=mock` until the backend has the
required settings. The API validates that live-mode settings are present at
startup. Restart the backend after changing environment values. Never commit
either `.env` file.

Set `WHATSAPP_PUBLIC_NUMBER` only after the intended sender is active and
ready. It controls the public Community click-to-chat link and must be the
displayable international phone number (for example `+250...`), not the Meta
Phone Number ID. The Community link stays unavailable while the provider is in
mock mode or the public number is missing or malformed.

## 4. Make the webhook reachable and configure it in Meta

Meta must be able to reach the backend over public HTTPS. A local address such
as `127.0.0.1:8000` is not reachable from Meta. For local development, use a
temporary HTTPS tunnel only for testing; for ongoing use, deploy the API behind
a stable HTTPS hostname.

In the Meta developer app, configure the WhatsApp Business Account webhook:

- **Callback URL:** `https://<public-api-host>/webhooks/whatsapp`
- **Verify token:** exactly the value in backend `WHATSAPP_VERIFY_TOKEN`
- **Subscribed field:** `messages`

The route supports Meta's GET verification challenge and POST event delivery.
POST requests are checked against the app secret using Meta's
`X-Hub-Signature-256` signature. Keep signature verification enabled. Subscribe
the WhatsApp Business Account to the app if the dashboard presents a separate
account-subscription step. Meta's
[Developer Hub](https://whatsappbusiness.com/developers/developer-hub/) links
to the current webhook documentation and test-event controls.

## 5. Test inbound messages and delivery events

Run the backend with the intended environment and use a test recipient first.
After the webhook is verified and subscribed:

1. Send a WhatsApp message to the configured test/business number.
2. Send `HELP` and confirm the bot responds with its command menu.
3. Try a supported command such as `DISTRICT <name>` or `LANG RW`.
4. Check the WhatsApp admin health and delivery views for received events and
   message status updates.
5. Confirm that `STOP` or `SHIRA` opts the contact out and prevents further
   alert dispatch until the person opts in again.

The bot currently supports `HELP`, `DISTRICT`, `CROP`, `SUBSCRIBE`, `STATUS`,
`RANK`, `ALERTS`, `LANG EN|RW`, and opt-out keywords. Unknown questions may use
the configured AI assistant; otherwise, the bot returns its command menu.

## 6. Approve and register alert templates

Business-initiated messages outside the customer-service window need a
matching approved template. Review
[`whatsapp_templates.md`](whatsapp_templates.md) for the current Agri-Menya
template names, languages, variables, and registry commands. Submit each
template in Meta's template manager, wait for approval, then mark only the
matching approved name and language as approved in Agri-Menya's registry.
Meta may change or reject template categories and content; follow the current
policy and the category Meta assigns. Do not mark a draft as approved merely
because it has been submitted.

Agri-Menya's alert flow requires consent, an active subscription, alert
approval, an available matching template when required, and the daily cap.
Test with a small, explicitly opted-in audience before dispatching broadly.

## 7. Move from test to live

Before setting `WHATSAPP_MODE=live` in a production deployment, confirm all of
the following:

- The intended business number and display name are active and ready in Meta.
- The production token is valid, securely stored, and has access to the
  selected WhatsApp assets.
- Backend environment values are present and the Graph API version is
  supported.
- The stable HTTPS webhook verifies and receives message/status events.
- Required templates have been approved in the exact languages used by
  Agri-Menya and recorded as approved in its template registry.
- User consent, opt-out handling, alert approvals, usage limits, and operational
  monitoring have been reviewed.

Changing `WHATSAPP_MODE` to `live` sends real WhatsApp messages and can incur
Meta charges under the then-current pricing rules. Keep live credentials out of
logs and frontend settings.

## Agri-Menya implementation references

- Backend settings: `backend/app/core/config.py`
- Cloud API sender: `backend/app/services/whatsapp/live.py`
- Inbound commands: `backend/app/services/whatsapp/bot.py`
- Webhook verification and processing: `backend/app/routers/webhooks.py`
- Consent-based alert dispatch: `backend/app/services/whatsapp/dispatcher.py`
- Template details and registry: [`whatsapp_templates.md`](whatsapp_templates.md)
- Admin controls: `backend/app/routers/whatsapp_admin.py` and the frontend
  **Communicate** view
