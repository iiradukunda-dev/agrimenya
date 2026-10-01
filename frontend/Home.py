import streamlit as st
import requests
from utils import api_client
from utils.theme import load_theme
from utils.i18n import t
from utils.timezone import setup_system_timezone
from components.icons import render_icon_title, render_icon_subheader
from components.navbar import render_navbar
from components.errors import render_error_page
st.set_page_config(page_title="Agri-Menya", page_icon="frontend/assets/logo.jpg", layout="wide")
setup_system_timezone()
load_theme()
render_navbar()

def main():
    render_icon_title("assets/wheat.svg", t("home.app_title"), t("home.subtitle"))
    
    st.markdown(t("home.welcome"))

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
            if not os.path.exists(icon):
                alt_icon = os.path.join("frontend", icon)
                if os.path.exists(alt_icon):
                    icon = alt_icon
            with open(icon, "r", encoding="utf-8") as f:
                svg_content = f.read()
            
            st.markdown(
                f"""
<div class="custom-card">
    <div style="width: 44px; height: 44px; border-radius: 10px; background-color: #E8F5E9; display: flex; align-items: center; justify-content: center; margin-bottom: 12px;">
        <div style="width: 24px; height: 24px; color: #52B788; display: flex; align-items: center; justify-content: center;">
            {svg_content}
        </div>
    </div>
    <div class="custom-card-title">{title}</div>
    <div class="custom-card-desc">{desc}</div>
</div>
<br/>
                """,
                unsafe_allow_html=True
            )
            if st.button(btn_text, use_container_width=True, key=f"btn_{page_route}"):
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
