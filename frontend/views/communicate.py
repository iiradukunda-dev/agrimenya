import requests
import streamlit as st
from components.alerts import render_alert
from components.errors import error_boundary, render_error_page
from components.icons import render_icon_title
from utils import api_client
from utils.i18n import t


@error_boundary("Communication")
def render_communicate():
    try:
        render_icon_title("assets/message.svg", t("comm.header"), t("comm.subtitle"))

        st.info(t("comm.info_notice", "agrimenya alerts are sent by administrators. This feed is available to community members for reading."))
        st.subheader(t("comm.feed_title"))
        alerts = api_client.get_alerts()
        if not alerts:
            st.info(t("comm.feed_empty"))
        else:
            for alert in alerts:
                render_alert(alert)

        with st.expander(t("comm.wa_admin", "WhatsApp administration"), expanded=False):
            st.caption("Manage contact consent and review alert delivery. Admin API access is required.")
            if not api_client.render_admin_login("wa_admin"):
                st.info("Administrator sign-in is required to manage WhatsApp contacts, consent, and alert dispatch.")
            else:
                health = api_client.get_whatsapp_health()
                if health:
                    h1, h2 = st.columns(2, gap="medium")
                    with h1:
                        st.metric("Provider mode", health.get("mode", "unknown"))
                        st.metric("Approved templates", health.get("approved_templates", 0))
                    with h2:
                        st.metric("Failed messages (24h)", health.get("failed_messages_24h", 0))
                        if health.get("last_webhook_received_at"):
                            st.caption(f"Last webhook: {health['last_webhook_received_at']}")
                else:
                    st.info("WhatsApp status is unavailable. Check the admin API key and backend connection.")

                stats = api_client.get_whatsapp_stats()
                if stats:
                    st.caption(f"Last {stats.get('days', 7)} days")
                    st.json({
                        "messages_by_status": stats.get("by_status", {}),
                        "messages_by_kind": stats.get("by_kind", {}),
                        "top_error_codes": stats.get("top_error_codes", {}),
                    })

                templates = api_client.get_whatsapp_templates()
                if templates:
                    st.markdown("**Registered templates**")
                    st.dataframe(templates, width="stretch", hide_index=True)
                    template_by_label = {
                        f"{item.get('name')} ({item.get('language')})": item
                        for item in templates
                    }
                    selected_template = template_by_label[
                        st.selectbox("Preview template", list(template_by_label), key="wa_template_preview")
                    ]
                    template_params = st.text_area(
                        f"Template values, one per line ({selected_template.get('param_count', 0)} required)",
                        key="wa_template_params",
                        placeholder="One value for each template parameter",
                    )
                    if st.button("Render template preview", key="wa_render_template"):
                        params = [value.strip() for value in template_params.splitlines() if value.strip()]
                        expected_count = int(selected_template.get("param_count") or 0)
                        if len(params) != expected_count:
                            st.error(f"This template requires {expected_count} non-empty values.")
                        else:
                            preview = api_client.preview_whatsapp_template(
                                selected_template["name"], selected_template["language"], params,
                            )
                            if preview:
                                st.info(preview.get("body_preview", "Preview unavailable."))
                            else:
                                st.error("Could not render the template preview. Check admin access.")

                contacts = api_client.get_whatsapp_contacts()
                left, right = st.columns([1, 1])
                with left:
                    st.markdown("**Contacts and consent**")
                    if contacts:
                        st.dataframe(
                            [
                                {
                                    "Name": c.get("display_name") or "Unnamed",
                                    "Role": c.get("role") or "-",
                                    "Phone": c.get("phone_masked") or "BSUID contact",
                                    "Language": c.get("language", "en"),
                                    "Opted in": c.get("whatsapp_opt_in", False),
                                }
                                for c in contacts if not c.get("deleted_at")
                            ],
                            width="stretch",
                            hide_index=True,
                        )
                    else:
                        st.caption("No contacts found, or contact access is unavailable.")

                    with st.form("whatsapp_create_contact"):
                        display_name = st.text_input("Contact name")
                        phone = st.text_input("Phone number", placeholder="0788123456 or +250788123456")
                        bsuid = st.text_input("WhatsApp BSUID (optional)")
                        role = st.selectbox("Role", ["farmer", "planner", "extension_officer", "cooperative_leader", "other"])
                        language = st.selectbox("Language", ["en", "rw"])
                        crops = st.text_input("Crops (comma separated)")
                        create_contact = st.form_submit_button("Add WhatsApp contact")
                        if create_contact:
                            payload = {
                                "display_name": display_name.strip() or None,
                                "phone": phone.strip() or None,
                                "bsuid": bsuid.strip() or None,
                                "role": role,
                                "language": language,
                                "crops": [crop.strip() for crop in crops.split(",") if crop.strip()],
                            }
                            if not payload["phone"] and not payload["bsuid"]:
                                st.error("Provide a phone number or BSUID.")
                            else:
                                result = api_client.create_whatsapp_contact(payload)
                                if result:
                                    st.success("Contact added.")
                                    st.rerun()
                                else:
                                    st.error("Could not add contact. Check for duplicate identity and admin access.")

                with right:
                    st.markdown("**Record consent and alert preferences**")
                    zones = api_client.get_zones() or []
                    zone_options = {}
                    for zone in zones:
                        if not zone.get("id"):
                            continue
                        label_parts = [
                            zone.get("district") or "Unknown district",
                            zone.get("sector") or zone.get("cell"),
                            zone.get("crop_type") or zone.get("crop"),
                        ]
                        label = " / ".join(str(part) for part in label_parts if part)
                        if label in zone_options:
                            label = f"{label} | {str(zone['id'])[:8]}"
                        zone_options[label] = zone["id"]

                    active_contacts = [c for c in contacts if not c.get("deleted_at")]
                    if active_contacts:
                        contact_labels = {
                            f"{c.get('display_name') or 'Unnamed'} · {c.get('phone_masked') or 'BSUID'} · {str(c['id'])[-8:]} · {'opted in' if c.get('whatsapp_opt_in') else 'not opted in'}": c
                            for c in active_contacts
                        }
                        chosen_label = st.selectbox("Contact", list(contact_labels), key="wa_contact_choice")
                        chosen_contact = contact_labels[chosen_label]
                        if not chosen_contact.get("whatsapp_opt_in"):
                            with st.form("whatsapp_opt_in"):
                                consent_source = st.text_input("Consent source", placeholder="Paper form, in-person, inbound WhatsApp")
                                consent_version = st.text_input("Consent text version", placeholder="opt-in-v1")
                                consent_submit = st.form_submit_button("Record opt-in")
                                if consent_submit:
                                    if not consent_source.strip() or not consent_version.strip():
                                        st.error("Enter the consent source and the text version used.")
                                    elif api_client.opt_in_whatsapp_contact(chosen_contact["id"], consent_source.strip(), consent_version.strip()):
                                        st.success("Consent recorded.")
                                        st.rerun()
                                    else:
                                        st.error("Could not record consent. Check admin access.")

                        with st.form("whatsapp_subscription"):
                            subscription_zone = st.selectbox(
                                "Alert zone",
                                ["All zones"] + list(zone_options),
                                key="wa_subscription_zone",
                            )
                            subscription_crop = st.text_input("Crop (optional)")
                            min_severity = st.selectbox("Minimum severity", ["info", "warning", "critical"], index=1)
                            subscription_submit = st.form_submit_button("Save alert preference")
                            if subscription_submit:
                                selected_zone_id = zone_options.get(subscription_zone)
                                result = api_client.subscribe_whatsapp_contact(
                                    chosen_contact["id"],
                                    {
                                        "zone_id": selected_zone_id,
                                        "crop": subscription_crop.strip() or None,
                                        "min_severity": min_severity,
                                    },
                                )
                                if result:
                                    st.success("Alert preference saved.")
                                else:
                                    st.error("Could not save the preference. Check admin access.")

                        if st.button("Remove contact", key="wa_remove_contact"):
                            if api_client.remove_whatsapp_contact(chosen_contact["id"]):
                                st.success("Contact removed.")
                                st.rerun()
                            else:
                                st.error("Could not remove contact.")
                    else:
                        st.caption("Add a contact to manage consent and alert preferences.")

                st.markdown("**Approve and dispatch an alert**")
                admin_alerts = api_client.get_admin_alerts()
                if admin_alerts:
                    alert_labels = {
                        f"{a.get('severity', 'Info')} · {a.get('message', '')[:90]} · {a.get('id')}": a
                        for a in admin_alerts if a.get("id")
                    }
                    if alert_labels:
                        selected_alert = alert_labels[st.selectbox("Alert", list(alert_labels), key="wa_alert_choice")]
                        alert_status = str(selected_alert.get("status", "")).lower()
                        if alert_status != "approved":
                            if st.button("Approve alert for WhatsApp", key="wa_approve_alert"):
                                result = api_client.approve_whatsapp_alert(selected_alert["id"])
                                if result:
                                    st.success("Alert approved for dispatch.")
                                    st.rerun()
                                else:
                                    detail = api_client.get_admin_api_error(f"/communication/alerts/{selected_alert['id']}/approve")
                                    st.error(f"Approval failed: {detail or 'the API did not return an explanation.'}")
                        else:
                            if st.button("Dispatch approved alert", key="wa_dispatch_alert"):
                                result = api_client.dispatch_whatsapp_alert(selected_alert["id"])
                                if result is not None:
                                    queued = result.get("queued", 0)
                                    failed = result.get("failed", 0)
                                    no_template = result.get("skipped_no_template", 0)
                                    no_consent = result.get("skipped_no_consent", 0)
                                    daily_cap = result.get("skipped_daily_cap", 0)
                                    if failed or no_template:
                                        st.warning(
                                            f"Dispatch finished with issues: {queued} queued, {failed} failed, "
                                            f"{no_template} skipped because no approved template is available, "
                                            f"{no_consent} skipped without consent, {daily_cap} skipped by the daily limit."
                                        )
                                        if no_template:
                                            st.caption("Approve the matching agrimenya_alert template in WhatsApp Manager and sync its status before retrying.")
                                    elif queued:
                                        st.success(f"Dispatch complete: {queued} message(s) queued; {no_consent} skipped without consent, {daily_cap} skipped by the daily limit.")
                                    elif no_consent or daily_cap:
                                        st.info(f"No messages were queued: {no_consent} contacts lacked eligible consent and {daily_cap} reached the daily limit.")
                                    else:
                                        st.info("No subscribed contacts matched this alert's zone, crop, and minimum severity.")
                                    if result.get("by_error_code"):
                                        st.caption("Provider error counts")
                                        st.json(result["by_error_code"])
                                else:
                                    detail = api_client.get_admin_api_error(f"/communication/alerts/{selected_alert['id']}/dispatch/whatsapp")
                                    st.error(f"Dispatch request failed: {detail or 'the API did not return an explanation.'}")
                            delivery = api_client.get_whatsapp_delivery(selected_alert["id"])
                            if delivery:
                                st.caption("Current delivery counts")
                                st.json(delivery.get("counts", {}))
                            else:
                                detail = api_client.get_admin_api_error(f"/communication/alerts/{selected_alert['id']}/delivery")
                                if detail:
                                    st.caption(f"Delivery counts unavailable: {detail}")
                else:
                    detail = api_client.get_admin_api_error("/admin/alerts")
                    if detail:
                        st.error(f"Could not load alerts: {detail}")
                    else:
                        st.caption("No alerts are available for WhatsApp approval.")
    except requests.exceptions.RequestException as e:
        import logging
        logging.getLogger(__name__).error(f"Network error in communicate.py: {e}")
        render_error_page("network", str(e))
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Unexpected error in communicate.py: {e}", exc_info=True)
        render_error_page("system", str(e))
