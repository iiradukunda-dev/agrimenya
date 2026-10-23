"""
Error page component - renders user-friendly error states.
"""
import os
from html import escape

import streamlit as st
from components.icons import get_base64_svg
from utils.i18n import t


def render_error_page(error_type: str, details: str = None) -> None:
    """
    Renders a modern user-friendly error page with contextual messaging.

    Args:
        error_type: One of '404', 'network', 'validation', 'system'.
        details: Optional technical detail string (shown in a code block).
    """
    title = t(f"error.{error_type}.title")
    desc = t(f"error.{error_type}.desc")

    # Try to load alert icon
    assets_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets"
    )
    icon_path = os.path.join(assets_dir, "alert.svg")

    icon_html = ""
    if os.path.exists(icon_path):
        try:
            icon_b64 = get_base64_svg(icon_path)
            icon_html = (
                f'<img src="data:image/svg+xml;base64,{icon_b64}" '
                f'style="width: 48px; height: 48px; margin-bottom: 16px;" />'
            )
        except Exception:
            pass

    if not icon_html:
        # Inline fallback SVG
        icon_html = """
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none"
             stroke="#52B788" stroke-width="2" stroke-linecap="round"
             stroke-linejoin="round" style="margin-bottom: 16px;">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
        """

    details_html = ""
    if details:
        details_html = f'<div class="ag-error-details">{escape(str(details))}</div>'

    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown(
            f"""
            <div class="ag-error-container">
                {icon_html}
                <h2>{title}</h2>
                <p>{desc}</p>
                {details_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            t("error.go_home"),
            width="stretch",
            key=f"btn_error_{error_type}",
        ):
            st.switch_page("Home.py")
