"""Feedback form for the agrimenya workspace."""
import os

import streamlit as st
from components.footer import render_footer
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
    st.markdown(
        """
        <style>
          .st-key-feedback_form_wrap {
            width: min(100%, 760px) !important;
            margin: 1.25rem auto 2rem !important;
          }
          .st-key-feedback_form_wrap [data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid #dce7ec !important;
            border-radius: 12px !important;
            background: #ffffff !important;
            box-shadow: 0 8px 24px rgba(16, 42, 52, 0.045) !important;
          }
          .st-key-feedback_form_wrap [data-testid="stFormSubmitButton"] {
            display: flex !important;
            justify-content: center !important;
          }
          [data-testid="stForm"] [data-testid="stFormSubmitButton"] button {
            width: min(100%, 360px) !important;
            min-height: 2.65rem !important;
            padding: 0.55rem 1.15rem !important;
            border: 1px solid #0875d1 !important;
            border-radius: 999px !important;
            background: #0875d1 !important;
            color: #ffffff !important;
            font-weight: 650 !important;
            box-shadow: 0 2px 7px rgba(8, 117, 209, 0.16) !important;
            transition: background-color 160ms ease, box-shadow 160ms ease,
                        transform 160ms ease !important;
          }
          [data-testid="stForm"] [data-testid="stFormSubmitButton"] button:hover {
            border: 2px solid #0875d1 !important;
            border-radius: 9999px !important;
            background: transparent !important;
            color: #0369a1 !important;
            box-shadow: none !important;
            transform: translateY(-2px) scale(1.02) !important;
          }
          [data-testid="stForm"] [data-testid="stFormSubmitButton"] button:focus-visible {
            outline: 3px solid rgba(8, 117, 209, 0.28) !important;
            outline-offset: 2px !important;
          }
          @media (max-width: 640px) {
            .st-key-feedback_form_wrap { width: 100% !important; }
            [data-testid="stForm"] [data-testid="stFormSubmitButton"] button {
              width: 100% !important;
            }
          }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container(key="feedback_form_wrap"):
        with st.container(border=True):
            st.title(t("contact.title", "Send feedback"))
            st.markdown(t("contact.subtitle", "Report an issue or share feedback about the agricultural data and workflows in this workspace."))
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

render_footer()


