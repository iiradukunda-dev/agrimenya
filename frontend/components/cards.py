"""Creative, animated workflow cards with rich micro-motions for the agrimenya frontend."""
import streamlit as st


def pillar_card(
    col,
    title: str,
    desc: str,
    btn_text: str,
    page_route: str,
    icon: str = "",
    tag: str = "WORKFLOW",
    accent_color: str = "#10b981",
) -> None:
    """Render an interactive, animated workflow card with fluid micro-motions."""
    with col:
        with st.container(border=True):
            icon_markup = (
                icon
                if icon
                else f"""<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{accent_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 14 14"></polyline></svg>"""
            )
            html_block = f"""
            <style>
            @keyframes ag-badge-pulse {{
                0%, 100% {{ transform: scale(1); box-shadow: 0 2px 8px {accent_color}25; }}
                50% {{ transform: scale(1.06); box-shadow: 0 0 16px {accent_color}55; }}
            }}
            .ag-workflow-icon-wrap {{
                width: 44px;
                height: 44px;
                border-radius: 12px;
                background: linear-gradient(135deg, {accent_color}25 0%, {accent_color}10 100%);
                border: 1.5px solid {accent_color}55;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 4px 14px {accent_color}30, inset 0 1px 1px rgba(255, 255, 255, 0.45);
                transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.35s cubic-bezier(0.16, 1, 0.3, 1), background 0.3s ease;
                will-change: transform, box-shadow;
            }}
            [data-testid="stVerticalBlockBorderWrapper"]:hover .ag-workflow-icon-wrap {{
                transform: translateY(-5px) scale(1.12) rotate(-4deg);
                box-shadow: 0 12px 26px {accent_color}55, inset 0 1px 2px rgba(255, 255, 255, 0.7);
                border-color: {accent_color}90;
            }}
            [data-testid="stVerticalBlockBorderWrapper"]:active .ag-workflow-icon-wrap {{
                transform: translateY(-1px) scale(1.02);
            }}
            .ag-workflow-tag {{
                font-size: 0.7rem;
                font-weight: 750;
                letter-spacing: 0.06em;
                text-transform: uppercase;
                color: {accent_color};
                background: {accent_color}22;
                padding: 3px 10px;
                border-radius: 9999px;
                border: 1px solid {accent_color}50;
                box-shadow: 0 2px 8px {accent_color}20;
                transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.35s ease, border-color 0.3s ease;
            }}
            [data-testid="stVerticalBlockBorderWrapper"]:hover .ag-workflow-tag {{
                transform: scale(1.05);
                box-shadow: 0 4px 14px {accent_color}45;
                border-color: {accent_color}90;
                animation: ag-badge-pulse 2s infinite ease-in-out;
            }}
            </style>
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.75rem;">
                <div class="ag-workflow-icon-wrap">{icon_markup}</div>
                <span class="ag-workflow-tag">{tag}</span>
            </div>
            <h3 style="margin:0.2rem 0 0.45rem;font-family:'Plus Jakarta Sans',sans-serif;font-size:1.15rem;font-weight:750;color:#ffffff;letter-spacing:-0.02em;text-shadow:0 2px 8px rgba(0,0,0,0.7);transition:color 0.25s ease;">{title}</h3>
            <p style="color:#e0f2fe;font-size:0.88rem;line-height:1.55;min-height:42px;margin:0 0 0.85rem;text-shadow:0 1px 6px rgba(0,0,0,0.7);">{desc}</p>
            """
            st.markdown(html_block, unsafe_allow_html=True)
            if st.button(f"{btn_text} →", key=f"btn_{page_route}", width="stretch"):
                st.switch_page(page_route)

