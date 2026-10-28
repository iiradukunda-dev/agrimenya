"""
Priority and status badge components - renders semantic status indicators.
"""
from html import escape
import streamlit as st
from utils.i18n import t


def priority_badge(priority: str) -> None:
    """
    Renders a modern semantic priority badge with a colored dot indicator.

    Args:
        priority: One of 'High', 'Medium', or 'Low'.
    """
    raw_priority = str(priority or "Unknown")
    normalized = raw_priority.lower().strip()
    if normalized not in {"high", "medium", "low"}:
        st.markdown(
            f'<div class="ag-badge ag-badge-unknown"><span class="ag-badge-dot"></span>{escape(raw_priority)}</div>',
            unsafe_allow_html=True,
        )
        return
    css_class = f"ag-badge ag-badge-{normalized}"
    display_text = escape(t(f"priority.{normalized}", default=raw_priority))

    html = f'<div class="{css_class}"><span class="ag-badge-dot"></span>{display_text}</div>'
    st.markdown(html, unsafe_allow_html=True)


def status_badge(text: str, variant: str = "info") -> None:
    """
    Renders a semantic status badge.
    
    Args:
        text: Display label
        variant: 'success' | 'warning' | 'high' | 'info' | 'unknown'
    """
    v_norm = variant.lower().strip()
    if v_norm in ("high", "urgent", "danger", "error"):
        cls = "ag-badge-high"
    elif v_norm in ("medium", "warning", "pending"):
        cls = "ag-badge-medium"
    elif v_norm in ("low", "success", "completed", "verified"):
        cls = "ag-badge-low"
    else:
        cls = "ag-badge-unknown"

    html = f'<div class="ag-badge {cls}"><span class="ag-badge-dot"></span>{escape(text)}</div>'
    st.markdown(html, unsafe_allow_html=True)
