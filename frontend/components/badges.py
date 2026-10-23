"""
Priority badge component - renders semantic status indicators.
"""
from html import escape

import streamlit as st
from utils.i18n import t


def priority_badge(priority: str) -> None:
    """
    Renders a modern semantic priority badge with a pulsing dot indicator.

    Args:
        priority: One of 'High', 'Medium', or 'Low'.
    """
    raw_priority = str(priority or "Unknown")
    normalized = raw_priority.lower()
    if normalized not in {"high", "medium", "low"}:
        st.markdown(f'<div class="ag-badge ag-badge-unknown">{escape(raw_priority)}</div>', unsafe_allow_html=True)
        return
    css_class = f"ag-badge ag-badge-{normalized}"
    display_text = escape(t(f"priority.{normalized}", default=raw_priority))

    html = f'<div class="{css_class}">{display_text}</div>'
    st.markdown(html, unsafe_allow_html=True)
