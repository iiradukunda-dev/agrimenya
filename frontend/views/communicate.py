import logging
from typing import Any
import requests
import streamlit as st
from components.alerts import render_alert
from components.badges import status_badge
from components.cards import render_kpi_card
from components.errors import error_boundary, render_error_page
from components.icons import render_icon_title
from utils import api_client
from utils.i18n import t

logger = logging.getLogger(__name__)


@error_boundary("Communication")
def render_communicate() -> None:
    try:
        render_icon_title(
            "assets/message.svg",
            t("comm.header", default="Communication & Alerts Hub"),
            t("comm.subtitle", default="Broadcast urgent field alerts, dispatch multi-channel SMS/WhatsApp/Email notifications, and manage farmer contacts."),
        )

        if st.session_state.pop("alert_sent_flash", False):
            st.success("Field alert published and broadcasted successfully.")
        if st.session_state.pop("notify_sent_flash", False):
            st.success("Multi-channel notification dispatched.")

        tab_alerts, tab_notify, tab_whatsapp = st.tabs([
            t("comm.tab_alerts", default="Community Alerts Bulletin"),
            t("comm.tab_notify", default="Multi-Channel Dispatch Engine"),
            t("comm.tab_whatsapp", default="WhatsApp Administration"),
        ])

        # ─────────────────────────────────────────────────────────────
        # TAB 1: ALERTS BULLETIN & BROADCAST
        # ─────────────────────────────────────────────────────────────
        with tab_alerts:
            col_feed, col_broadcast = st.columns([1.6, 1.2], gap="large")

            with col_feed:
                st.subheader(t("comm.feed_title", default="Active Community Alerts"))
                st.caption(t("comm.feed_caption", default="Real-time agronomic and weather warnings issued to extension agents and farmers."))

                severity_filter = st.selectbox(
                    "Filter by Severity",
                    options=["All Severities", "Urgent", "Warning", "Info"],
                    index=0,
                    key="filter_alert_sev",
                )

                alerts = api_client.get_alerts()
                if not alerts:
                    st.info(t("comm.feed_empty", default="No active community alerts at this time."))
                else:
                    filtered_alerts = [
                        a for a in alerts
                        if severity_filter == "All Severities" or str(a.get("type", "")).casefold() == severity_filter.casefold()
                    ]
                    if not filtered_alerts:
                        st.caption(f"No alerts matching '{severity_filter}'.")
                    else:
                        for alert in filtered_alerts:
                            render_alert(alert)

            with col_broadcast:
                st.subheader(t("comm.broadcast_title", default="Broadcast Field Alert"))
                st.caption(t("comm.broadcast_caption", default="Publish a localized alert that appears in the feed and broadcasts to registered farmers."))

                zones = api_client.get_zones()
                zone_choices = {
                    f"{z.get('district', 'Unknown district')} / {z.get('sector') or z.get('cell') or z.get('id')}": z.get("id")
                    for z in zones if z.get("id")
                }

                if not zone_choices:
                    st.info("No active zones available to target alerts.")
                else:
                    with st.form("broadcast_alert_form", border=True):
                        target_zone = st.selectbox("Target Agricultural Area", list(zone_choices), key="bcast_zone")
                        zone_id = str(zone_choices[target_zone])
                        severity = st.selectbox("Severity Level", ["Warning", "Urgent", "Info"], index=0, key="bcast_sev")
                        crops = ["All Crops"] + (api_client.get_crops() or ["Maize", "Beans", "Cassava", "Irish Potatoes", "Rice"])
                        selected_crop = st.selectbox("Target Crop (optional)", crops, key="bcast_crop")
                        crop_val = None if selected_crop == "All Crops" else selected_crop

                        recommended_action = st.text_input("Recommended Farmer Action", placeholder="e.g. Apply fungicide immediately before expected rainfall", key="bcast_action")
                        alert_msg = st.text_area("Alert Advisory Message", placeholder="Detail the threat, affected sectors, and immediate guidance...", key="bcast_msg")

                        send_alert_btn = st.form_submit_button("Broadcast Alert", type="primary", use_container_width=True)

                    if send_alert_btn:
                        if not alert_msg.strip():
                            st.warning("Please enter an alert message before broadcasting.")
                        else:
                            with st.spinner("Publishing alert and sending email broadcasts..."):
                                res = api_client.send_alert(
                                    message=alert_msg.strip(),
                                    zone_id=zone_id,
                                    severity=severity,
                                    crop=crop_val,
                                    action=recommended_action.strip() if recommended_action.strip() else None,
                                )
                            if res:
                                st.session_state["alert_sent_flash"] = True
                                api_client.get_alerts.clear()
                                st.rerun()
                            else:
                                st.error("Failed to broadcast alert. If this endpoint requires administrative credentials, ensure admin tools are unlocked.")

        # ─────────────────────────────────────────────────────────────
        # TAB 2: MULTI-CHANNEL DISPATCH ENGINE
        # ─────────────────────────────────────────────────────────────
        with tab_notify:
            st.subheader(t("comm.notify_title", default="Multi-Channel Notification Dispatch"))
            st.caption(t("comm.notify_caption", default="Directly dispatch urgent SMS, WhatsApp, and Email advisories to cooperative managers or extension officers."))

            # Delivery Channel Status Row
            email_info = api_client.get_email_status() or {}
            wa_info = api_client.get_whatsapp_status_info() or {}

            c_email_stat, c_wa_stat, c_sms_stat = st.columns(3)
            with c_email_stat:
                render_kpi_card(
                    title="SMTP Email Gateway",
                    value="Operational" if email_info.get("ready") else "Mock / Local",
                    subtitle=f"Port {email_info.get('port', 587)} ({email_info.get('transport', 'TLS')})",
                )
            with c_wa_stat:
                render_kpi_card(
                    title="WhatsApp Cloud API",
                    value="Live Ready" if wa_info.get("ready") else "Simulated",
                    subtitle=f"Mode: {wa_info.get('mode', 'mock')}",
                )
            with c_sms_stat:
                render_kpi_card(
                    title="Twilio SMS Channel",
                    value="Configured",
                    subtitle="Direct Mobile Carrier Gate",
                )

            st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)

            with st.form("multi_channel_notify_form", border=True):
                st.markdown("##### Outbound Notification Parameters")
                col_p, col_e = st.columns(2)
                with col_p:
                    n_phone = st.text_input("Recipient Mobile Phone", placeholder="+250788123456", key="n_phone_input", help="Include country code, e.g. +250")
                with col_e:
                    n_email = st.text_input("Recipient Email", placeholder="cooperative.leader@gmail.com", key="n_email_input")

                selected_channels = st.multiselect(
                    "Delivery Channels",
                    options=["sms", "whatsapp", "email"],
                    default=["sms", "email"],
                    key="n_channels_input",
                )

                n_message = st.text_area(
                    "Advisory Text",
                    placeholder="e.g. Heavy rain advisory for Musanze: Store harvested potatoes in elevated structures immediately.",
                    key="n_msg_input",
                    height=100,
                )

                send_notify_btn = st.form_submit_button("Send Multi-Channel Notification", type="primary", use_container_width=True)

            if send_notify_btn:
                if not n_message.strip():
                    st.warning("Please provide a message to transmit.")
                elif not selected_channels:
                    st.warning("Please select at least one delivery channel.")
                else:
                    payload = {
                        "message": n_message.strip(),
                        "channels": selected_channels,
                    }
                    if n_phone.strip():
                        payload["phone"] = n_phone.strip()
                    if n_email.strip():
                        payload["email"] = n_email.strip()

                    with st.spinner("Transmitting notification across selected channels..."):
                        notify_result = api_client.notify(payload)

                    if notify_result:
                        overall_status = notify_result.get("status", "unknown")
                        deliveries = notify_result.get("deliveries", {})

                        st.success(f"Transmission Status: **{overall_status.upper()}**")
                        for ch, info in deliveries.items():
                            with st.container(border=True):
                                col_cname, col_cstat, col_creason = st.columns([1, 1, 2])
                                with col_cname:
                                    st.markdown(f"**{ch.upper()}**")
                                with col_cstat:
                                    status_badge(info.get("status", "unknown"))
                                with col_creason:
                                    if info.get("reason"):
                                        st.caption(f"Note: {info.get('reason')}")
                                    elif info.get("message_sid"):
                                        st.caption(f"SID: {info.get('message_sid')}")
                    else:
                        st.error("Notification could not be dispatched. Verify backend connectivity and rate limits.")

        # ─────────────────────────────────────────────────────────────
        # TAB 3: WHATSAPP ADMINISTRATION
        # ─────────────────────────────────────────────────────────────
        with tab_whatsapp:
            st.subheader(t("comm.wa_admin", default="WhatsApp Administration & Farmer Registry"))
            st.caption("Manage farmer opt-in consent, preview registered Meta templates, and audit delivery metrics.")

            if not api_client.render_admin_login("comm_wa_admin"):
                st.info("Administrator authentication is required to access WhatsApp subscriber contacts and dispatch tools.")
            else:
                from components.whatsapp_admin import render_whatsapp_admin_panel
                render_whatsapp_admin_panel(key_prefix="comm_wa_panel", embedded_mode=True)

    except requests.exceptions.RequestException as e:
        logger.error("Network error in communicate.py: %s", e)
        render_error_page("network", str(e))
    except Exception as e:
        logger.error("Unexpected error in communicate.py: %s", e, exc_info=True)
        render_error_page("system", str(e))
