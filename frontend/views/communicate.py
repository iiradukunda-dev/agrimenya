import requests
import streamlit as st
from components.alerts import render_alert
from components.errors import render_error_page
from components.icons import render_icon_title
from utils import api_client
from utils.i18n import t


def render_communicate():
    try:
        render_icon_title("assets/message.svg", t("comm.header"), t("comm.subtitle"))

        feedback = st.session_state.pop("alert_delivery_feedback", None)
        if feedback:
            delivery_status = feedback.get("status")
            details = ", ".join(
                f"{channel}: {result.get('status', 'unknown')}"
                for channel, result in feedback.get("deliveries", {}).items()
            )
            if delivery_status in {"sent", "accepted"}:
                st.success(f"Alert recorded. Provider status: {details or delivery_status}.")
            else:
                st.warning(f"Alert recorded, but notification delivery is {delivery_status}. {details}")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader(t("comm.feed_title"))
            alerts = api_client.get_alerts()
            if not alerts:
                st.info(t("comm.feed_empty"))
            else:
                for alert in alerts:
                    render_alert(alert)

        with col2:
            st.subheader(t("comm.share_title"))
            zones = api_client.get_zones()
            zone_options = {
                f"{z.get('district', 'Unknown district')} / {z.get('sector') or z.get('cell') or z.get('id')}": z.get("id")
                for z in zones
            }
            if not zone_options:
                st.info("Create or load a zone before creating an alert.")
                return
            with st.form("share_form"):
                selected_zone = st.selectbox("Zone", list(zone_options))
                severity = st.selectbox("Severity", ["Info", "Warning", "Critical"])
                message = st.text_area(t("comm.message_label"))
                submitted = st.form_submit_button(t("comm.send_btn"))
                
                if submitted:
                    if message:
                        result = api_client.send_alert(message, zone_options[selected_zone], severity)
                        if result:
                            st.session_state["alert_delivery_feedback"] = result.get("notification", {})
                            st.rerun()
                        else:
                            st.error("Failed to send alert. Please try again.")
                    else:
                        st.error(t("comm.error_empty"))
    except requests.exceptions.RequestException as e:
        import logging
        logging.getLogger(__name__).error(f"Network error in communicate.py: {e}")
        render_error_page("network", str(e))
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Unexpected error in communicate.py: {e}", exc_info=True)
        render_error_page("system", str(e))
