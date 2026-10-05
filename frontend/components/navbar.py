"""
Navigation bar component for agrimenya.

Renders a floating glass navigation bar with branding, page links,
and an inline language selector. Uses a data-driven link list to keep
the layout easy to maintain.
"""

from typing import List, Tuple

import streamlit as st
from utils.i18n import render_language_selector


# Central registry of navbar links: (page_path, label, material_icon)
_NAV_LINKS: List[Tuple[str, str, str]] = [
    ("Home.py", "Home", "home"),
    ("pages/3_Dashboard.py", "Dashboard", "dashboard"),
    ("pages/4_Zones.py", "Zones", "map"),
    ("pages/5_Segmentation.py", "Segment", "layers"),
    ("pages/6_Decision_Making.py", "Decide", "bolt"),
    ("pages/7_AI_Assistant.py", "AI", "smart_toy"),
    ("pages/8_Planning.py", "Plan", "edit_calendar"),
    ("pages/9_Communication.py", "Alerts", "campaign"),
    ("pages/10_Admin.py", "Admin", "admin_panel_settings"),
]


def _inject_navbar_styles() -> None:
    """Inject CSS that hides default Streamlit chrome and styles the glass pill."""
    st.markdown("""
        <style>
        /* Hide default Streamlit navigation chrome */
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }
        header[data-testid="stHeader"] { display: none !important; }

        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
        }

        /* Floating glass pill for the first horizontal block */
        .stMainBlockContainer > div > div > [data-testid="stHorizontalBlock"]:first-child {
            background: rgba(255, 255, 255, 0.35) !important;
            backdrop-filter: blur(24px) saturate(180%) !important;
            -webkit-backdrop-filter: blur(24px) saturate(180%) !important;
            border: 1px solid rgba(255, 255, 255, 0.45) !important;
            border-radius: 50px !important;
            padding: 6px 20px !important;
            box-shadow:
                0 4px 20px rgba(0, 0, 0, 0.05),
                inset 0 1px 0 rgba(255, 255, 255, 0.6) !important;
            align-items: center !important;
            margin: 0 auto 2rem auto !important;
            max-width: 1200px !important;
            gap: 0 !important;
        }

        /* Compact page-link buttons inside the navbar */
        .stMainBlockContainer > div > div > [data-testid="stHorizontalBlock"]:first-child
            [data-testid="stPageLink-NavLink"] {
            font-size: 0.82rem !important;
            padding: 4px 6px !important;
        }
        </style>
    """, unsafe_allow_html=True)


def _render_brand(col: st.delta_generator.DeltaGenerator) -> None:
    """Render the agrimenya logo text in the given column."""
    with col:
        st.markdown(
            '<p style="font-family: \'Space Grotesk\', sans-serif; font-weight: 800; '
            'font-size: 1.25rem; margin: 0; padding: 4px 0; white-space: nowrap; '
            'background: linear-gradient(135deg, #2D6A4F, #52B788); '
            '-webkit-background-clip: text; -webkit-text-fill-color: transparent;">'
            'agrimenya</p>',
            unsafe_allow_html=True,
        )


def render_navbar() -> None:
    """
    Render a premium floating navigation bar with agrimenya branding.

    The navbar is built from a central ``_NAV_LINKS`` list so that adding,
    removing, or reordering pages only requires editing one place.
    """
    _inject_navbar_styles()

    # Column widths: brand (wider) + one col per link + language selector
    link_count = len(_NAV_LINKS)
    col_widths = [1.5] + [1.0] * link_count + [0.5]
    cols = st.columns(col_widths)

    # Brand
    _render_brand(cols[0])

    # Page links
    for idx, (path, label, icon) in enumerate(_NAV_LINKS, start=1):
        with cols[idx]:
            st.page_link(path, label=label, icon=f":material/{icon}:")

    # Language selector (icon-only)
    with cols[-1]:
        render_language_selector(sidebar=False)

    st.divider()
