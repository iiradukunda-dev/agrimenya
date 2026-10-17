"""Feedback form for the agrimenya workspace."""
import os

import streamlit as st
from components.navbar import render_navbar
from utils import api_client
from utils.theme import load_theme

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "logo.jpg")

st.set_page_config(page_title="Feedback - agrimenya", page_icon=LOGO_PATH, layout="wide")
load_theme()
render_navbar()

st.title("Send feedback")
st.markdown("Report an issue or share feedback about the agricultural data and workflows in this workspace.")

with st.container(border=True):
    with st.form("contact_form", clear_on_submit=True):
        name = st.text_input("Name", max_chars=120)
        email = st.text_input("Email address", max_chars=254)
        subject = st.text_input("Subject", max_chars=160)
        message = st.text_area("Message", height=180, max_chars=5000)
        submitted = st.form_submit_button("Send feedback", type="primary", width="stretch")

if submitted:
    if not name.strip() or not email.strip() or not message.strip():
        st.error("Enter your name, email address, and message.")
    else:
        response = api_client.send_contact_message(name.strip(), email.strip(), subject.strip(), message.strip())
        if response:
            st.success("Your feedback was submitted.")
        else:
            st.error("Feedback could not be submitted. Please try again when the service is available.")
