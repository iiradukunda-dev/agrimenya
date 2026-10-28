"""Executive Stakeholder Communication & Alerts Hub."""
import logging
import streamlit as st
from components.alerts import render_alert
from components.errors import error_boundary
from components.icons import render_icon_title
from components.whatsapp_admin import render_whatsapp_admin_panel
from utils import api_client
from utils.i18n import t

logger = logging.getLogger(__name__)


@st.dialog("Broadcast Field Alert")
def show_broadcast_dialog() -> None:
    """Popup modal for broadcasting an alert without cluttering the main page."""
    zones = api_client.get_zones()
    zone_choices = {
        f"{z.get('district', 'District')} / {z.get('sector') or z.get('cell') or z.get('id')}": str(z.get("id"))
        for z in zones if z.get("id")
    }

    if not zone_choices:
        st.info("No active agricultural zones available to target.")
        return

    with st.form("broadcast_alert_modal_form", border=False):
        c1, c2 = st.columns(2)
        with c1:
            target_zone = st.selectbox("Target Area", list(zone_choices), key="modal_bcast_zone")
        with c2:
            severity = st.selectbox("Severity", ["Warning", "Urgent", "Info"], index=0, key="modal_bcast_sev")

        crops = ["All Crops"] + (api_client.get_crops() or ["Maize", "Beans", "Cassava", "Irish Potatoes", "Rice"])
        selected_crop = st.selectbox("Crop (optional)", crops, key="modal_bcast_crop")
        crop_val = None if selected_crop == "All Crops" else selected_crop

        action = st.text_input("Recommended Action", placeholder="e.g. Apply fungicide before rain", key="modal_bcast_act")
        msg = st.text_area("Alert Message", placeholder="Detail the threat and required action...", key="modal_bcast_msg", height=90)

        submitted = st.form_submit_button("Send Broadcast", type="primary", use_container_width=True)

    if submitted:
        if not msg.strip():
            st.warning("Please enter an alert message.")
            return

        zone_id = zone_choices[target_zone]
        res = api_client.send_alert(
            message=msg.strip(),
            zone_id=zone_id,
            severity=severity,
            crop=crop_val,
            action=action.strip() if action.strip() else None,
        )
        if res:
            st.session_state["alert_sent_flash"] = True
            api_client.get_alerts.clear()
            st.rerun()
        else:
            st.error("Failed to broadcast alert. Check administrative credentials.")


@error_boundary("Communication")
def render_communicate() -> None:
    try:
        render_icon_title(
            "assets/message.svg",
            t("comm.header", default="Alerts & Messaging"),
            t("comm.subtitle", default="Direct agronomic bulletins and messaging gateway."),
        )

        if st.session_state.pop("alert_sent_flash", False):
            st.success("Alert broadcasted successfully.")

        tab_alerts, tab_whatsapp = st.tabs([
            t("comm.tab_alerts", default="Community Alerts"),
            t("comm.tab_whatsapp", default="WhatsApp Messaging"),
        ])

        with tab_alerts:
            c_header, c_btn = st.columns([3, 1])
            with c_header:
                st.subheader(t("comm.feed_title", default="Active Bulletins"))
            with c_btn:
                if st.button("+ Broadcast Alert", type="primary", use_container_width=True):
                    show_broadcast_dialog()

            # Compact severity filter pills
            filter_sev = st.pills(
                "Filter",
                options=["All", "Urgent", "Warning", "Info"],
                default="All",
                label_visibility="collapsed",
                key="alert_sev_pills",
            )

            alerts = api_client.get_alerts()
            if not alerts:
                st.info(t("comm.feed_empty", default="No active bulletins at this time."))
            else:
                filtered = [
                    a for a in alerts
                    if filter_sev == "All" or str(a.get("type", "")).casefold() == filter_sev.casefold()
                ]
                if not filtered:
                    st.caption(f"No alerts matching '{filter_sev}'.")
                else:
                    for alert in filtered:
                        render_alert(alert)

        with tab_whatsapp:
            render_whatsapp_admin_panel()

    except Exception as exc:
        logger.exception("Error rendering communication page: %s", exc)
        render_error_page(exc)
