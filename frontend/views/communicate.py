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
                from components.whatsapp_admin import render_whatsapp_admin_panel
                render_whatsapp_admin_panel(key_prefix="comm_wa", embedded_mode=True)
    except requests.exceptions.RequestException as e:
        import logging
        logging.getLogger(__name__).error(f"Network error in communicate.py: {e}")
        render_error_page("network", str(e))
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Unexpected error in communicate.py: {e}", exc_info=True)
        render_error_page("system", str(e))
