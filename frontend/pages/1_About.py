import os

import streamlit as st
from components.navbar import render_navbar
from utils.theme import load_theme

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "ai_assistant_bulb.png")

st.set_page_config(page_title="agrimenya", page_icon=LOGO_PATH, layout="wide", initial_sidebar_state="collapsed")
load_theme()
render_navbar()

st.title("About agrimenya")
st.markdown("A workspace for agricultural teams to review zone information and organise local action.")

st.markdown("## How the workspace is organised")
sections = [
    ("Zones and segmentation", "Browse registered areas and compare the crop, season, production, and priority information available for each zone."),
    ("Decisions", "Review recommendations returned by the connected service. Use the accompanying zone context before acting on a recommendation."),
    ("Planning", "Create a zone-specific plan with actions, notes, and timing agreed by your team."),
    ("Communication", "Review alerts and use the configured communication channels and consent workflows."),
    ("Farmer community", "Share field experiences and questions with other growers; community roles are not yet verified."),
]
for start in range(0, len(sections), 2):
    columns = st.columns(2, gap="medium")
    for col, (heading, description) in zip(columns, sections[start : start + 2]):
        with col:
            with st.container(border=True):
                st.markdown(f"### {heading}")
                st.write(description)

st.markdown("## Reading the information")
st.write("Values depend on the records and services currently connected to this workspace. An unavailable value means the backend did not provide it; it should not be read as zero. Forecasts and model outputs are estimates and should be checked against local conditions and qualified agricultural advice.")
st.caption("The application uses a Streamlit frontend connected to the agrimenya API. Features and available data depend on the active deployment configuration.")
