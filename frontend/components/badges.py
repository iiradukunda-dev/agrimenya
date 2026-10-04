"""
Priority badge component — renders semantic status indicators.
"""
import streamlit as st
from utils.i18n import t


def priority_badge(priority: str) -> None:
    """
    Renders a glassmorphic priority badge with a pulsing dot indicator.

    Args:
        priority: One of 'High', 'Medium', or 'Low'.
    """
    css_class = f"ag-badge ag-badge-{priority.lower()}"
    display_text = t(f"priority.{priority.lower()}", default=priority)

    html = f'<div class="{css_class}">{display_text}</div>'
    st.markdown(html, unsafe_allow_html=True)
