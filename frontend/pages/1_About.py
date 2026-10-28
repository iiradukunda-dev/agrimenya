import os

import streamlit as st
from components.errors import error_boundary
from components.navbar import render_navbar
from utils.i18n import t
from utils.theme import load_theme

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "ai_assistant_bulb.png")

st.set_page_config(page_title="agrimenya", page_icon=LOGO_PATH, layout="wide", initial_sidebar_state="collapsed")
load_theme()
render_navbar()

with error_boundary("About agrimenya"):
    st.title(t("about.title", "About agrimenya"))
    st.markdown(t("about.subtitle", "A workspace for agricultural teams to review zone information and organise local action."))

    st.markdown(f"## {t('about.sections_title', 'How the workspace is organised')}")
    sections = [
        (t("about.sec.zones_title", "Zones and segmentation"), t("about.sec.zones_desc", "Browse registered areas and compare the crop, season, production, and priority information available for each zone.")),
        (t("about.sec.decisions_title", "Decisions"), t("about.sec.decisions_desc", "Review recommendations returned by the connected service. Use the accompanying zone context before acting on a recommendation.")),
        (t("about.sec.planning_title", "Planning"), t("about.sec.planning_desc", "Create a zone-specific plan with actions, notes, and timing agreed by your team.")),
        (t("about.sec.comm_title", "Communication"), t("about.sec.comm_desc", "Review alerts and use the configured communication channels and consent workflows.")),
        (t("about.sec.community_title", "Farmer community"), t("about.sec.community_desc", "Share field experiences and questions with other growers; community roles are not yet verified.")),
    ]
    for start in range(0, len(sections), 2):
        columns = st.columns(2, gap="medium")
        for col, (heading, description) in zip(columns, sections[start : start + 2]):
            with col:
                with st.container(border=True):
                    st.markdown(f"### {heading}")
                    st.write(description)

    st.markdown(f"## {t('about.reading_title', 'Reading the information')}")
    st.write(t("about.reading_desc", "Values depend on the records and services currently connected to this workspace. An unavailable value means the backend did not provide it; it should not be read as zero. Forecasts and model outputs are estimates and should be checked against local conditions and qualified agricultural advice."))
    st.caption(t("about.caption", "The application uses a Streamlit frontend connected to the agrimenya API. Features and available data depend on the active deployment configuration."))


