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
        val = kpis.get('total_farmers', 'N/A')
        st.metric(t("home.kpi.farmers"), f"{val:,}" if isinstance(val, (int, float)) else val)
    with col2:
        st.metric(t("home.kpi.yield"), kpis.get('yield_increase', 'N/A'))
    with col3:
        val = kpis.get('active_cooperatives', 'N/A')
        st.metric(t("home.kpi.cooperatives"), f"{val:,}" if isinstance(val, (int, float)) else val)

    st.divider()

    render_icon_subheader("assets/compass.svg", t("home.pillars_title"))
    c1, c2, c3, c4 = st.columns(4)

    def pillar_card(col, icon, title, desc, btn_text, page_route):
        with col:
            import os
            icon_path = icon
            if icon_path.startswith("assets/") or icon_path.startswith("assets\\"):
                assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
                icon_path = os.path.join(assets_dir, os.path.basename(icon_path))

            try:
                with open(icon_path, "r", encoding="utf-8") as f:
                    svg_content = f.read()
            except FileNotFoundError:
                svg_content = ""

            st.html(
                f"""
<div class="ag-card">
    <div class="ag-card-icon">
        <div style="width: 26px; height: 26px; color: #40916C; display: flex; align-items: center; justify-content: center;">
            {svg_content}
        </div>
    </div>
    <div class="ag-card-title">{title}</div>
    <div class="ag-card-desc">{desc}</div>
</div>
<br/>
                """
            )
            if st.button(btn_text, key=f"btn_{page_route}"):
                st.switch_page(page_route)

    pillar_card(
        c1, 
        "assets/map.svg", 
        t("pillar.segmentation.title"), 
        t("pillar.segmentation.desc"), 
        t("pillar.segmentation.btn"), 
        "pages/3_Segmentation.py"
    )
    pillar_card(
        c2, 
        "assets/brain.svg", 
        t("pillar.decisions.title"), 
        t("pillar.decisions.desc"), 
        t("pillar.decisions.btn"), 
        "pages/1_Decision_Making.py"
    )
    pillar_card(
        c3, 
        "assets/calendar.svg", 
        t("pillar.planification.title"), 
        t("pillar.planification.desc"), 
        t("pillar.planification.btn"), 
        "pages/2_Planification.py"
    )
    pillar_card(
        c4, 
        "assets/message.svg", 
        t("pillar.communication.title"), 
        t("pillar.communication.desc"), 
        t("pillar.communication.btn"), 
        "pages/4_Communication.py"
    )
    
    st.divider()
    st.caption(t("common.built_for"))

try:
    main()
except requests.exceptions.RequestException as e:
    render_error_page("network", str(e))
except Exception as e:
    render_error_page("system", str(e))
