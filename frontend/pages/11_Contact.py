"""Feedback form for the agrimenya workspace."""
import os

import streamlit as st
from components.errors import error_boundary
from components.navbar import render_navbar
from utils import api_client
from utils.i18n import t
from utils.theme import load_theme

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "ai_assistant_bulb.png")

st.set_page_config(page_title="agrimenya", page_icon=LOGO_PATH, layout="wide", initial_sidebar_state="collapsed")
load_theme()
render_navbar()

with error_boundary("Feedback & Support"):
    st.title(t("contact.title", "Send feedback"))
    st.markdown(t("contact.subtitle", "Report an issue or share feedback about the agricultural data and workflows in this workspace."))

    with st.container(border=True):
        with st.form("contact_form", clear_on_submit=True):
            name = st.text_input(t("contact.name", "Name"), max_chars=120)
            email = st.text_input(t("contact.email", "Email address"), max_chars=254)
            subject = st.text_input(t("contact.subject", "Subject"), max_chars=160)
            message = st.text_area(t("contact.message", "Message"), height=180, max_chars=5000)
            submitted = st.form_submit_button(t("contact.submit", "Send feedback"), type="primary", width="stretch")

    if submitted:
        if not name.strip() or not email.strip() or not message.strip():
            st.error(t("contact.err_required", "Enter your name, email address, and message."))
        else:
            response = api_client.send_contact_message(name.strip(), email.strip(), subject.strip(), message.strip())
            if response:
                st.success(t("contact.success", "Your feedback was submitted."))
            else:
                st.error(t("contact.err_send", "Feedback could not be submitted. Please try again when the service is available."))


