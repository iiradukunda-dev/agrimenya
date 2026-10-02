"""
About page — mission, team, and platform overview.
"""
import streamlit as st
import os
from utils.theme import load_theme
from utils.i18n import t
from components.navbar import render_navbar
from components.icons import render_icon_title

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "logo.jpg")

st.set_page_config(page_title="About agrimenya", page_icon=LOGO_PATH, layout="wide")
load_theme()
render_navbar()


def main() -> None:
    render_icon_title("assets/info.svg", "About agrimenya", "Learn more about our mission and platform")

    # ── Mission Statement ──────────────────────────────────────
    st.markdown("""
    ### Our Mission
    agrimenya is designed to empower agricultural professionals, cooperatives, and planners
    with data-driven insights. By leveraging advanced analytics and seamless communication
    channels, we aim to optimize resource allocation, enhance crop yields, and foster
    collaboration across the agricultural ecosystem.
    """)

    st.divider()

    # ── Core Pillars ───────────────────────────────────────────
    st.markdown("### Core Pillars")
    c1, c2, c3, c4 = st.columns(4)

    pillar_data = [
        (c1, "🧠", "Decide",
         "AI-powered recommendations for interventions based on priority levels and historical data."),
        (c2, "📅", "Plan",
         "Interactive roadmaps to track seasonal tasks and ensure timely execution of activities."),
        (c3, "🗺️", "Segment",
         "Geographic insights and yield mapping to identify high-potential areas and allocate resources."),
        (c4, "📡", "Communicate",
         "Real-time alerts and unified messaging to connect extension officers, cooperatives, and planners."),
    ]

    for col, icon, title, desc in pillar_data:
        with col:
            st.html(f"""
            <div class="ag-card" style="min-height: 200px;">
                <div style="font-size: 2rem; margin-bottom: 12px;">{icon}</div>
                <div class="ag-card-title">{title}</div>
                <div class="ag-card-desc">{desc}</div>
            </div>
            """)

    st.divider()

    # ── Tech Stack ─────────────────────────────────────────────
    st.markdown("### Technology")
    st.markdown("""
    agrimenya is built on a modern, scalable architecture:

    - **Backend**: FastAPI with XGBoost ML models for crop yield prediction and priority ranking
    - **Frontend**: Streamlit with a custom Liquid Glass design system, React/GSAP interactive components
    - **Database**: PostgreSQL via Supabase for real-time data sync
    - **Deployment**: Dockerised microservices orchestrated with Docker Compose
    """)


main()
