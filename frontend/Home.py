import os

import requests
import streamlit as st
from components.animated_hero import render_react_hero
from components.errors import render_error_page
from components.icons import render_icon_subheader
from components.navbar import render_navbar
from utils import api_client
from utils.i18n import t
from utils.theme import load_theme
from utils.timezone import setup_system_timezone

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "logo.jpg")

st.set_page_config(page_title="agrimenya", page_icon=LOGO_PATH, layout="wide")
setup_system_timezone()
load_theme()
render_navbar()

def main():
    # Render interactive React Hero with GSAP
    render_react_hero()

    # High-level KPIs
    kpis = api_client.get_kpis()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Registered zones", f"{kpis['total_zones']:,}")
    with col2:
        baseline = kpis.get("baseline_yield_kg_ha")
        st.metric("Baseline yield", f"{baseline:,.0f} kg/ha" if isinstance(baseline, (int, float)) else "N/A")
    with col3:
        st.metric("Alerts", kpis["active_alerts"] if kpis.get("active_alerts") is not None else "N/A")

    st.divider()

    render_icon_subheader("assets/compass.svg", t("home.pillars_title"))
    c1, c2, c3, c4 = st.columns(4)

    from components.cards import pillar_card

    pillar_card(
        c1, 
        "assets/map.svg", 
        t("pillar.segmentation.title"), 
        t("pillar.segmentation.desc"), 
        t("pillar.segmentation.btn"), 
        "pages/5_Segmentation.py"
    )
    pillar_card(
        c2, 
        "assets/brain.svg", 
        t("pillar.decisions.title"), 
        t("pillar.decisions.desc"), 
        t("pillar.decisions.btn"), 
        "pages/6_Decision_Making.py"
    )
    pillar_card(
        c3, 
        "assets/calendar.svg", 
        t("pillar.planification.title"), 
        t("pillar.planification.desc"), 
        t("pillar.planification.btn"), 
        "pages/8_Planning.py"
    )
    pillar_card(
        c4, 
        "assets/message.svg", 
        t("pillar.communication.title"), 
        t("pillar.communication.desc"), 
        t("pillar.communication.btn"), 
        "pages/9_Communication.py"
    )
    
    st.divider()
    st.caption(t("common.built_for"))

if __name__ == "__main__":
    import logging
    logger = logging.getLogger(__name__)
    try:
        main()
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error in Home.py: {e}")
        render_error_page("network", str(e))
    except Exception as e:
        logger.error(f"Unexpected error in Home.py: {e}", exc_info=True)
        render_error_page("system", str(e))
