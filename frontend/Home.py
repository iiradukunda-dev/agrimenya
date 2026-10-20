import os

import streamlit as st
from components.cards import pillar_card
from components.home_hero import render_home_hero
from components.navbar import render_navbar
from utils.theme import load_theme
from utils.timezone import setup_system_timezone

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "logo.jpg")

st.set_page_config(page_title="agrimenya - Agro-Climate Decision Support", page_icon=LOGO_PATH, layout="wide")
setup_system_timezone()
load_theme()
render_navbar()


def main():
    # Animated command-center hero section
    render_home_hero()

    # Section 1: Core Action Workflows
    st.markdown(
        """<div style="margin:1.8rem 0 1rem;display:flex;align-items:flex-end;justify-content:space-between;flex-wrap:wrap;gap:0.5rem;"><div><h2 style="margin:0;font-family:'Plus Jakarta Sans',sans-serif;font-size:1.65rem;font-weight:800;color:#032b35;letter-spacing:-0.03em;">Decision & Action Pillars</h2><p style="margin:0.25rem 0 0;color:#3e5c66;font-size:0.94rem;">Navigate from spatial zone intelligence to verified field recommendations and team dispatches.</p></div></div>""",
        unsafe_allow_html=True,
    )

    workflows = [
        (
            "Explore Zones",
            "Browse 30 registered districts, evaluate soil indicators, and inspect historical SAS crop data.",
            "Open zones",
            "pages/4_Zones.py",
            """<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"></polygon><line x1="9" y1="3" x2="9" y2="18"></line><line x1="15" y1="6" x2="15" y2="21"></line></svg>""",
            "SPATIAL SAS",
            "#0284c7",
        ),
        (
            "Review Priorities",
            "Examine evidence-grounded crop recommendations, yield intervals, and intervention trade-offs.",
            "Review decisions",
            "pages/6_Decision_Making.py",
            """<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>""",
            "DECISION ENGINE",
            "#10b981",
        ),
        (
            "Build Seasonal Plan",
            "Organise seasonal milestones, team responsibilities, and resource allocations for each zone.",
            "Open planning",
            "pages/8_Planning.py",
            """<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#0ea5e9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>""",
            "FIELD TIMELINE",
            "#0ea5e9",
        ),
        (
            "Coordinate Updates",
            "Review district climate alerts and broadcast approved advisories to extension agents via WhatsApp/SMS.",
            "Open communication",
            "pages/9_Communication.py",
            """<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#06b6d4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 11 18-5-5 18-4-7-9-6z"></path><path d="m14 13-5 5"></path></svg>""",
            "BROADCAST HUB",
            "#06b6d4",
        ),
    ]

    cards = st.columns(4, gap="medium")
    for col, (title, description, action, route, icon, tag, accent) in zip(cards, workflows):
        pillar_card(col, title, description, action, route, icon=icon, tag=tag, accent_color=accent)

    # Section 2: Interactive Operational Roadmap
    st.markdown(
        """<div style="margin:2.6rem 0 1.2rem;"><div style="display:inline-flex;align-items:center;gap:6px;padding:4px 12px;background:rgba(14,165,233,0.12);border:1px solid rgba(56,189,248,0.3);border-radius:9999px;font-size:0.74rem;font-weight:750;letter-spacing:0.08em;text-transform:uppercase;color:#0284c7;">OPERATIONAL PIPELINE</div><h2 style="margin:0.4rem 0 0.25rem;font-family:'Plus Jakarta Sans',sans-serif;font-size:1.55rem;font-weight:800;color:#032b35;letter-spacing:-0.03em;">A Practical Field Workflow</h2><p style="margin:0;color:#3e5c66;font-size:0.94rem;">A streamlined three-stage cycle designed for agronomists, regional planners, and extension leaders.</p></div>""",
        unsafe_allow_html=True,
    )

    steps = st.columns(3, gap="medium")
    step_data = [
        (
            "01",
            "Target Area & Baseline",
            "Select a target district, sector, and crop variety to review official SAS baselines and local soil parameters.",
            """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="22" y1="12" x2="18" y2="12"></line><line x1="6" y1="12" x2="2" y2="12"></line><line x1="12" y1="6" x2="12" y2="2"></line><line x1="12" y1="22" x2="12" y2="18"></line></svg>""",
            "#0284c7",
        ),
        (
            "02",
            "Evaluate Evidence Matrix",
            "Cross-reference rainfall forecasts, soil moisture indicators, and conformal yield confidence intervals.",
            """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>""",
            "#10b981",
        ),
        (
            "03",
            "Coordinate Field Response",
            "Lock seasonal action items into operational plans and broadcast urgent WhatsApp/email advisories to local agents.",
            """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0ea5e9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2L11 13"></path><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>""",
            "#0ea5e9",
        ),
    ]

    for col, (num, title, desc, icon, color) in zip(steps, step_data):
        with col:
            with st.container(border=True):
                step_html = (
                    f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.75rem;">'
                    f'<span style="font-family:\'Plus Jakarta Sans\',sans-serif;font-size:1.3rem;font-weight:800;color:{color};background:{color}14;border:1px solid {color}30;border-radius:10px;padding:2px 10px;">{num}</span>'
                    f'<span style="display:flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:8px;background:{color}14;border:1px solid {color}30;">{icon}</span>'
                    f'</div>'
                    f'<h3 style="margin:0 0 0.45rem;font-family:\'Plus Jakarta Sans\',sans-serif;font-size:1.1rem;font-weight:750;color:#032b35;letter-spacing:-0.02em;">{title}</h3>'
                    f'<p style="color:#3e5c66;font-size:0.88rem;line-height:1.6;margin:0;">{desc}</p>'
                )
                st.markdown(step_html, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
