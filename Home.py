import streamlit as st
from utils import api_client
from components.icons import render_icon_title, render_icon_subheader

st.set_page_config(page_title="Agri-Menya", page_icon="assets/wheat.svg", layout="wide")

render_icon_title("assets/wheat.svg", "Agri-Menya", "Decision and Planning Support System for Agricultural Productivity")

st.markdown("""
Welcome to **Agri-Menya**. This platform empowers planners, extension officers, and cooperative leaders with data-driven insights using SAS, AHS, and EICV7 datasets.
""")

# High-level KPIs
kpis = api_client.get_kpis()
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Farmers Supported", f"{kpis['total_farmers']:,}")
with col2:
    st.metric("Avg Yield Increase", kpis['yield_increase'])
with col3:
    st.metric("Active Cooperatives", f"{kpis['active_cooperatives']:,}")

st.divider()

render_icon_subheader("assets/compass.svg", "Core Pillars")
c1, c2, c3, c4 = st.columns(4)

def pillar_card(col, icon, title, desc, btn_text, page_route):
    with col:
        st.markdown(
            f"""<div style="background-color:#f8f9fa; padding:16px; border-radius:8px; height:120px;">
            <b>{title}</b><br/><span style="color:#666;">{desc}</span></div>""",
            unsafe_allow_html=True
        )
        if st.button(btn_text, use_container_width=True, key=f"btn_{title}"):
            st.switch_page(page_route)

pillar_card(c1, "assets/map.svg", "Segmentation", "Identify high-priority zones based on yield and risk data.", "Go to Segmentation", "pages/3_Segmentation.py")
pillar_card(c2, "assets/brain.svg", "Decision Making", "Review automated recommendations for timely interventions.", "Go to Decisions", "pages/1_Decision_Making.py")
pillar_card(c3, "assets/calendar.svg", "Planification", "Plan and track agricultural roadmaps and execution.", "Go to Planification", "pages/2_Planification.py")
pillar_card(c4, "assets/message.svg", "Communication", "Share alerts, plans, and coordinate with stakeholders.", "Go to Communication", "pages/4_Communication.py")

st.divider()
st.caption("Built for the 2026 NISR Big Data Hackathon")
