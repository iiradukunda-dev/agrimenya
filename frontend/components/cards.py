"""Creative, animated workflow cards for the agrimenya frontend."""
import streamlit as st


def pillar_card(
    col,
    title: str,
    desc: str,
    btn_text: str,
    page_route: str,
    icon: str = "🌾",
    tag: str = "WORKFLOW",
    accent_color: str = "#10b981",
) -> None:
    """Render an interactive, animated glass workflow card."""
    with col:
        with st.container(border=True):
            html_block = f"""<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.75rem;"><div style="width:42px;height:42px;border-radius:12px;background:{accent_color}1a;border:1px solid {accent_color}40;display:flex;align-items:center;justify-content:center;font-size:1.3rem;box-shadow:0 4px 12px {accent_color}18;">{icon}</div><span style="font-size:0.7rem;font-weight:750;letter-spacing:0.06em;text-transform:uppercase;color:{accent_color};background:{accent_color}14;padding:3px 9px;border-radius:9999px;border:1px solid {accent_color}25;">{tag}</span></div><h3 style="margin:0.2rem 0 0.45rem;font-family:'Plus Jakarta Sans',sans-serif;font-size:1.15rem;font-weight:750;color:#0f2d1e;letter-spacing:-0.02em;">{title}</h3><p style="color:#4b6354;font-size:0.88rem;line-height:1.6;min-height:60px;margin:0 0 0.9rem;">{desc}</p>"""
            st.markdown(html_block, unsafe_allow_html=True)
            if st.button(f"{btn_text} →", key=f"btn_{page_route}", width="stretch"):
                st.switch_page(page_route)
