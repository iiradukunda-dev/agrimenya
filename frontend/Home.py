import os

import streamlit as st
from components.cards import pillar_card
from components.errors import error_boundary
from components.footer import render_footer
from components.home_hero import render_home_hero
from components.navbar import render_navbar
from utils.i18n import t
from utils.theme import load_theme
from utils.timezone import setup_system_timezone

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "ai_assistant_bulb.png")

st.set_page_config(page_title="agrimenya", page_icon=LOGO_PATH, layout="wide", initial_sidebar_state="collapsed")
setup_system_timezone()
load_theme()
render_navbar()


def main():
    # Animated command-center hero section
    render_home_hero()

    # Section 1: Core Action Workflows
    workflows_title = t("home.workflows_title", "What would you like to work on?")
    workflows_sub = t("home.workflows_sub", "Pick a starting point. You can explore a district, review crop information, or plan what to do next.")

    st.markdown(
        f"""<div style="margin:2rem 0 1rem;display:flex;align-items:flex-end;justify-content:space-between;flex-wrap:wrap;gap:0.5rem;"><div><h2 class="ag-section-title" style="color:#0a1f26;font-family:'Plus Jakarta Sans',sans-serif;font-size:1.65rem;font-weight:800;letter-spacing:-0.03em;margin:0;">{workflows_title}</h2><p class="ag-section-subtitle" style="color:#48656c;font-size:0.94rem;margin:0.25rem 0 0;">{workflows_sub}</p></div></div>""",
        unsafe_allow_html=True,
    )

    workflows = [
        (
            t("home.workflow.zones_title", "Explore Zones"),
            t("home.workflow.zones_desc", "Get to know a district and explore the local information available."),
            t("home.workflow.zones_btn", "Explore zones"),
            "pages/4_Zones.py",
            """<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#527c5d" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"></polygon><line x1="9" y1="3" x2="9" y2="18"></line><line x1="15" y1="6" x2="15" y2="21"></line></svg>""",
            "EXPLORE",
            "#527c5d",
        ),
        (
            t("home.workflow.decisions_title", "Compare Crop Options"),
            t("home.workflow.decisions_desc", "Compare crop options and review the information behind each recommendation."),
            t("home.workflow.decisions_btn", "See recommendations"),
            "pages/6_Decision_Making.py",
            """<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#75885e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>""",
            "COMPARE",
            "#75885e",
        ),
        (
            t("home.workflow.plan_title", "Plan Your Season"),
            t("home.workflow.plan_desc", "Turn your priorities into a seasonal schedule your team can follow."),
            t("home.workflow.plan_btn", "Make a plan"),
            "pages/8_Planning.py",
            """<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#b2762d" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>""",
            "PLAN",
            "#b2762d",
        ),
        (
            t("home.workflow.comm_title", "Share Field Updates"),
            t("home.workflow.comm_desc", "Share timely updates and coordinate with people working in the field."),
            t("home.workflow.comm_btn", "Share an update"),
            "pages/9_Communication.py",
            """<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#577f83" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 11 18-5-5 18-4-7-9-6z"></path><path d="m14 13-5 5"></path></svg>""",
            "KEEP IN TOUCH",
            "#577f83",
        ),
    ]

    cards = st.columns(4, gap="medium")
    for col, (title, description, action, route, icon, tag, accent) in zip(cards, workflows):
        pillar_card(col, title, description, action, route, icon=icon, tag=tag, accent_color=accent)

    # Section 2: Interactive Operational Roadmap
    pipeline_badge = t("home.pipeline_badge", "A SIMPLE WAY TO GET STARTED")
    pipeline_title = t("home.pipeline_title", "From local insight to a shared plan")
    pipeline_sub = t("home.pipeline_sub", "Take it one step at a time. Start with the place, look at what you know, then decide together what comes next.")

    st.markdown(
        f"""
        <style>
        @keyframes ag-glow-line {{
            0%, 100% {{ opacity: 0.75; filter: drop-shadow(0 0 6px rgba(56, 189, 248, 0.4)); }}
            50% {{ opacity: 1; filter: drop-shadow(0 0 12px rgba(56, 189, 248, 0.75)); }}
        }}
        .ag-pipeline-badge {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 5px 14px;
            background: #edf3eb;
            border: 1px solid rgba(47, 94, 67, 0.15);
            border-radius: 9999px;
            font-size: 0.74rem;
            font-weight: 750;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #426b4e;
            box-shadow: none;
            animation: none;
        }}
        .ag-pipeline-beacon {{
            width: 7px;
            height: 7px;
            background: #527c5d;
            border-radius: 50%;
            box-shadow: none;
            animation: none;
        }}
        .ag-step-icon {{
            display: flex;
            align-items: center;
            justify-content: center;
            width: 36px;
            height: 36px;
            border-radius: 10px;
            background: #f4f7f3;
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
            <h2 class="ag-section-title" style="color:#0a1f26;font-family:'Plus Jakarta Sans',sans-serif;font-size:1.65rem;font-weight:800;letter-spacing:-0.03em;margin-top:0.45rem !important;">{pipeline_title}</h2>
            <p class="ag-section-subtitle" style="color:#48656c;font-size:0.94rem;margin:0.25rem 0 0;">{pipeline_sub}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    steps = st.columns(4, gap="medium")
    step_data = [
        (
            "01",
            t("home.step1_title", "Choose an area"),
            t("home.step1_desc", "Select a district and crop to see the local information available."),
            """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="22" y1="12" x2="18" y2="12"></line><line x1="6" y1="12" x2="2" y2="12"></line><line x1="12" y1="6" x2="12" y2="2"></line><line x1="12" y1="22" x2="12" y2="18"></line></svg>""",
        ),
        (
            "02",
            t("home.step2_title", "Review what you know"),
            t("home.step2_desc", "Look over rainfall, soil, and crop information before deciding."),
            """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>""",
        ),
        (
            "03",
            t("home.step3_title", "Make a seasonal plan"),
            t("home.step3_desc", "Agree on practical tasks and timing with your team."),
            """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>""",
        ),
        (
            "04",
            t("home.step4_title", "Keep everyone in the loop"),
            t("home.step4_desc", "Share useful updates with the people working in the field."),
            """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0ea5e9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2L11 13"></path><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>""",
        ),
    ]

    for col, (num, title, desc, icon) in zip(steps, step_data):
        with col:
            with st.container(border=True):
                step_html = (
                    f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.75rem;">'
                    f'<span style="font-family:\'Plus Jakarta Sans\',sans-serif;font-size:1.15rem;font-weight:750;color:#426b4e;background:#edf3eb;border:1px solid rgba(47,94,67,0.12);border-radius:10px;padding:3px 10px;">{num}</span>'
                    f'<span class="ag-step-icon" style="border:1px solid rgba(47,94,67,0.12);">{icon}</span>'
                    f'</div>'
                    f'<h3 style="margin:0 0 0.45rem;font-family:\'Plus Jakarta Sans\',sans-serif;font-size:1.05rem;font-weight:700;color:#1f3025;letter-spacing:-0.02em;">{title}</h3>'
                    f'<p style="color:#52645a;font-size:0.88rem;line-height:1.55;margin:0;">{desc}</p>'
                )
                st.markdown(step_html, unsafe_allow_html=True)

    st.markdown(
        '<div style="margin-top:2.5rem;padding-top:1.25rem;border-top:1px solid var(--ag-border);text-align:center;">'
        '<p style="margin:0 0 0.25rem;color:var(--ag-text-muted);font-size:0.9rem;">Help us improve agrimenya</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <style>
          .st-key-home_feedback_link { display: flex; justify-content: center; }
          .st-key-home_feedback_link a {
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 0.45rem !important;
            min-height: 2.65rem !important;
            padding: 0.55rem 1rem !important;
            border: 1px solid #d5e2e7 !important;
            border-radius: 999px !important;
            background: #ffffff !important;
            color: #315d70 !important;
            font-size: 0.9rem !important;
            font-weight: 650 !important;
            text-decoration: none !important;
            box-shadow: 0 2px 7px rgba(16, 42, 52, 0.06) !important;
            transition: border-color 160ms ease, color 160ms ease,
                        background-color 160ms ease, transform 160ms ease !important;
          }
          .st-key-home_feedback_link a:hover {
            border-color: #1682bb !important;
            background: #f3f9fc !important;
            color: #126c9b !important;
            transform: translateY(-1px) !important;
          }
          .st-key-home_feedback_link a:focus-visible {
            outline: 3px solid rgba(22, 130, 187, 0.3) !important;
            outline-offset: 2px !important;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )
    with st.container(key="home_feedback_link"):
        st.page_link(
            "pages/11_Contact.py",
            label=t("home.send_feedback", "Send feedback"),
            icon=":material/feedback:",
        )


if __name__ == "__main__":
    with error_boundary("Home"):
        main()
    render_footer()
