import streamlit as st
import requests
from utils.i18n import t
from utils import api_client
from components.alerts import render_alert
from components.icons import render_icon_title
from components.errors import render_error_page

def render_communicate():
    try:
        render_icon_title("assets/message.svg", t("comm.header"), t("comm.subtitle"))

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
            with st.form("share_form"):
                audience_options = [
                    t("comm.audience.extension"),
                    t("comm.audience.coop"),
                    t("comm.audience.planners"),
                    t("comm.audience.all")
                ]
                target_group = st.selectbox(t("comm.target_audience"), audience_options)
                message = st.text_area(t("comm.message_label"))
                is_urgent = st.checkbox(t("comm.is_urgent"))
                submitted = st.form_submit_button(t("comm.send_btn"))
                
                if submitted:
                    if message:
                        success = api_client.send_alert(message, target_group, is_urgent)
                        if success:
                            st.success(t("comm.success", group=target_group))
                            st.rerun()
                        else:
                            st.error("Failed to send alert. Please try again.")
                    else:
                        st.error(t("comm.error_empty"))
    except requests.exceptions.RequestException as e:
        render_error_page("network", str(e))
    except Exception as e:
        render_error_page("system", str(e))
