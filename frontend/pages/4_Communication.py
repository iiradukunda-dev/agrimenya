import streamlit as st
from frontend.utils.theme import load_theme
from frontend.utils import api_client
from frontend.components.alerts import render_alert
from frontend.components.icons import render_icon_title

st.set_page_config(page_title="Communication", page_icon="frontend/assets/message.svg", layout="wide")
load_theme()

render_icon_title("frontend/assets/message.svg", "Efficient Communication", "Real-time alerts, updates, and coordination across stakeholders.")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Alert Feed")
    alerts = api_client.get_alerts()
    if not alerts:
        st.info("No new alerts or the backend could not be reached.")
    else:
        for alert in alerts:
            render_alert(alert)

with col2:
    st.subheader("Share Information")
    with st.form("share_form"):
        target_group = st.selectbox("Target Audience", ["Extension Officers", "Cooperative Leaders", "Government Planners", "All Stakeholders"])
        message = st.text_area("Message / Announcement")
        is_urgent = st.checkbox("Mark as Urgent")
        submitted = st.form_submit_button("Send Update")
        
        if submitted:
            if message:
                st.success(f"Message sent to {target_group}!")
            else:
                st.error("Please enter a message.")
