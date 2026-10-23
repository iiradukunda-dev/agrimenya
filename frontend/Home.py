import os

import streamlit as st
from components.cards import pillar_card
from components.home_hero import render_home_hero
from components.navbar import render_navbar
from utils.i18n import t
from utils.theme import load_theme
from utils.timezone import setup_system_timezone

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "ai_assistant_bulb.png")

st.set_page_config(page_title="agrimenya", page_icon=LOGO_PATH, layout="wide")
setup_system_timezone()
load_theme()
render_navbar()


def main():
    # Animated command-center hero section
    render_home_hero()

    # Section 1: Core Action Workflows
    workflows_title = t("home.workflows_title", "Decision & Action Pillars")
    workflows_sub = t("home.workflows_sub", "Navigate from spatial zone intelligence to verified field recommendations and team dispatches.")

    st.markdown(
        f"""<div style="margin:2rem 0 1rem;display:flex;align-items:flex-end;justify-content:space-between;flex-wrap:wrap;gap:0.5rem;"><div><h2 class="ag-section-title" style="color:#ffffff !important;-webkit-text-fill-color:#ffffff !important;text-shadow:0 2px 10px rgba(0,0,0,0.8);font-family:'Plus Jakarta Sans',sans-serif;font-size:1.65rem;font-weight:800;letter-spacing:-0.03em;margin:0;">{workflows_title}</h2><p class="ag-section-subtitle" style="color:#e0f2fe !important;-webkit-text-fill-color:#e0f2fe !important;text-shadow:0 1px 6px rgba(0,0,0,0.8);font-size:0.94rem;margin:0.25rem 0 0;">{workflows_sub}</p></div></div>""",
        unsafe_allow_html=True,
    )

    workflows = [
        (
            t("home.workflow.zones_title", "Explore Zones"),
            t("home.workflow.zones_desc", "Browse 30 districts, soil metrics, and SAS yield history."),
            t("home.workflow.zones_btn", "Open zones"),
            "pages/4_Zones.py",
            """<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"></polygon><line x1="9" y1="3" x2="9" y2="18"></line><line x1="15" y1="6" x2="15" y2="21"></line></svg>""",
            "SPATIAL SAS",
            "#0284c7",
        ),
        (
            t("home.workflow.decisions_title", "Review Priorities"),
            t("home.workflow.decisions_desc", "Evaluate crop recommendations and conformal yield bounds."),
            t("home.workflow.decisions_btn", "Review decisions"),
            "pages/6_Decision_Making.py",
            """<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>""",
            "DECISION ENGINE",
            "#10b981",
        ),
        (
            t("home.workflow.plan_title", "Build Seasonal Plan"),
            t("home.workflow.plan_desc", "Structure district timelines, tasks, and field milestones."),
            t("home.workflow.plan_btn", "Open planning"),
            "pages/8_Planning.py",
            """<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#0ea5e9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>""",
            "FIELD TIMELINE",
            "#0ea5e9",
        ),
        (
            t("home.workflow.comm_title", "Coordinate Updates"),
            t("home.workflow.comm_desc", "Broadcast climate alerts and advisories via WhatsApp/SMS."),
            t("home.workflow.comm_btn", "Open communication"),
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
    pipeline_badge = t("home.pipeline_badge", "OPERATIONAL PIPELINE")
    pipeline_title = t("home.pipeline_title", "A Practical Field Workflow")
    pipeline_sub = t("home.pipeline_sub", "A structured four-stage cycle designed for agronomists, regional planners, and extension leaders.")

    st.markdown(
        f"""
        <style>
        @keyframes ag-glow-line {{
            0%, 100% {{ opacity: 0.75; filter: drop-shadow(0 0 6px rgba(56, 189, 248, 0.4)); }}
            50% {{ opacity: 1; filter: drop-shadow(0 0 14px rgba(74, 222, 128, 0.7)); }}
        }}
        .ag-pipeline-badge {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 5px 14px;
            background: linear-gradient(135deg, rgba(14, 165, 233, 0.28) 0%, rgba(16, 185, 129, 0.22) 100%);
            border: 1px solid rgba(56, 189, 248, 0.55);
            border-radius: 9999px;
            font-size: 0.74rem;
            font-weight: 750;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #7dd3fc;
            box-shadow: 0 4px 14px rgba(2, 24, 36, 0.4);
            animation: ag-glow-line 4s infinite ease-in-out;
        }}
        .ag-pipeline-beacon {{
            width: 7px;
            height: 7px;
            background: #38bdf8;
            border-radius: 50%;
            box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.8);
            animation: ag-radar-ping 2s infinite cubic-bezier(0, 0, 0.2, 1);
        }}
        .ag-step-icon {{
            display: flex;
            align-items: center;
            justify-content: center;
            width: 36px;
            height: 36px;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.1);
            transition: transform 0.35s ease;
        }}
        [data-testid="stVerticalBlockBorderWrapper"]:hover .ag-step-icon {{
            transform: scale(1.14) rotate(6deg);
        }}
        </style>
        <div style="margin:2.8rem 0 1.2rem;">
            <div class="ag-pipeline-badge">
                <span class="ag-pipeline-beacon"></span>
                {pipeline_badge}
            </div>
            <h2 class="ag-section-title" style="color:#ffffff !important;-webkit-text-fill-color:#ffffff !important;text-shadow:0 2px 10px rgba(0,0,0,0.8);font-family:'Plus Jakarta Sans',sans-serif;font-size:1.65rem;font-weight:800;letter-spacing:-0.03em;margin-top:0.45rem !important;">{pipeline_title}</h2>
            <p class="ag-section-subtitle" style="color:#e0f2fe !important;-webkit-text-fill-color:#e0f2fe !important;text-shadow:0 1px 6px rgba(0,0,0,0.8);font-size:0.94rem;margin:0.25rem 0 0;">{pipeline_sub}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    steps = st.columns(4, gap="medium")
    step_data = [
        (
            "01",
            t("home.step1_title", "Target Area & Baseline"),
            t("home.step1_desc", "Select district and crop to review official SAS baselines."),
            """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="22" y1="12" x2="18" y2="12"></line><line x1="6" y1="12" x2="2" y2="12"></line><line x1="12" y1="6" x2="12" y2="2"></line><line x1="12" y1="22" x2="12" y2="18"></line></svg>""",
            "#0284c7",
        ),
        (
            "02",
            t("home.step2_title", "Evaluate Evidence Matrix"),
            t("home.step2_desc", "Assess rain forecasts, soil moisture, and yield bounds."),
            """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>""",
            "#10b981",
        ),
        (
            "03",
            t("home.step3_title", "Build Seasonal Plan"),
            t("home.step3_desc", "Structure district timelines, tasks, and field milestones."),
            """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>""",
            "#f59e0b",
        ),
        (
            "04",
            t("home.step4_title", "Coordinate Field Response"),
            t("home.step4_desc", "Assign seasonal action items and notify field agents."),
            """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0ea5e9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2L11 13"></path><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>""",
            "#0ea5e9",
        ),
    ]

    for col, (num, title, desc, icon, color) in zip(steps, step_data):
        with col:
            with st.container(border=True):
                step_html = (
                    f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.75rem;">'
                    f'<span style="font-family:\'Plus Jakarta Sans\',sans-serif;font-size:1.3rem;font-weight:800;color:#ffffff;background:{color}28;border:1px solid {color}55;border-radius:10px;padding:2px 10px;box-shadow:0 2px 8px {color}35;transition:all 0.3s ease;">{num}</span>'
                    f'<span class="ag-step-icon" style="border:1px solid {color}50;">{icon}</span>'
                    f'</div>'
                    f'<h3 style="margin:0 0 0.45rem;font-family:\'Plus Jakarta Sans\',sans-serif;font-size:1.1rem;font-weight:750;color:#ffffff;letter-spacing:-0.02em;text-shadow:0 2px 8px rgba(0,0,0,0.7);">{title}</h3>'
                    f'<p style="color:#e0f2fe;font-size:0.88rem;line-height:1.55;margin:0;text-shadow:0 1px 6px rgba(0,0,0,0.7);">{desc}</p>'
                )
                st.markdown(step_html, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
