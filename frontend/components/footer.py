"""Shared site footer for agrimenya pages."""
from datetime import date

import streamlit as st


def render_footer() -> None:
    """Render a quiet, responsive copyright footer at the end of a page."""
    year = date.today().year
    st.markdown(
        f"""
        <style>
          .ag-site-footer {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 0.5rem 1rem;
            margin: 2.5rem 0 0.5rem;
            padding: 1rem 0.2rem 0.35rem;
            border-top: 1px solid var(--ag-border, #dbe5ec);
            color: var(--ag-text-subtle, #64748b);
            font: 0.78rem/1.5 var(--ag-font-sans, Inter, sans-serif);
          }}
          .ag-site-footer strong {{
            color: var(--ag-text-muted, #334155);
            font-weight: 700;
          }}
          @media (max-width: 560px) {{
            .ag-site-footer {{
              justify-content: center;
              text-align: center;
              margin-top: 1.75rem;
              padding-top: 0.85rem;
            }}
          }}
        </style>
        <footer class="ag-site-footer" aria-label="Copyright">
          <span><strong>agrimenya</strong> · Agricultural insights for local decisions</span>
          <span>© {year} youthInspire · agrimenya. All rights reserved.</span>
        </footer>
        """,
        unsafe_allow_html=True,
    )
