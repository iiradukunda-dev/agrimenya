"""Plain-language guide to interpreting data in agrimenya."""
import os

import streamlit as st
from components.navbar import render_navbar
from utils.i18n import t
from utils.theme import load_theme

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "ai_assistant_bulb.png")

st.set_page_config(page_title="agrimenya", page_icon=LOGO_PATH, layout="wide", initial_sidebar_state="collapsed")
load_theme()
render_navbar()

st.title(t("guide.title", "Data guide"))
st.markdown(t("guide.subtitle", "A short guide to what the workspace shows and how to read it."))

guide = [
    (t("guide.sec.zones_title", "Zones"), t("guide.sec.zones_desc", "A zone is an agricultural area recorded in the system. District, sector or cell, crop, season, area, and location are shown only when those details are available.")),
    (t("guide.sec.priorities_title", "Priorities and recommendations"), t("guide.sec.priorities_desc", "These come from the connected backend. A priority is a signal for review; check its zone and crop context before planning an intervention.")),
    (t("guide.sec.production_title", "Production and yield"), t("guide.sec.production_desc", "Production predictions and yield baselines are different measures. The interface labels each value and leaves it unavailable when the service has no value.")),
    (t("guide.sec.weather_title", "Weather"), t("guide.sec.weather_desc", "Weather information is associated with the selected district. Forecast values are estimates for a district location; a fallback snapshot is marked when current provider data cannot be reached.")),
    (t("guide.sec.plans_title", "Plans"), t("guide.sec.plans_desc", "Saved plans contain actions entered by a user for a selected zone. Confirm timing, resources, and responsibilities with the people carrying out the work.")),
    (t("guide.sec.alerts_title", "Alerts and WhatsApp"), t("guide.sec.alerts_desc", "Alert delivery depends on recipient consent, approved templates, and the configured messaging service. A saved alert does not by itself mean that a message was delivered.")),
]
for start in range(0, len(guide), 2):
    cols = st.columns(2, gap="medium")
    for col, (heading, explanation) in zip(cols, guide[start : start + 2]):
        with col:
            with st.container(border=True):
                st.markdown(f"### {heading}")
                st.write(explanation)

st.info(t("guide.disclaimer", "Model outputs and forecasts support review. Confirm decisions with current field observations and qualified local advice."))

