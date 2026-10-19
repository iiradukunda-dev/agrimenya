"""Floating AI Assistant widget visible across all pages."""
import base64
import os
import streamlit as st

_ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
_IMAGE_PATH = os.path.join(_ASSETS_DIR, "ai_assistant_bulb.png")


@st.cache_data
def _get_ai_icon_base64() -> str:
    """Return base64 encoded string of the AI Assistant lightbulb icon."""
    if os.path.exists(_IMAGE_PATH):
        with open(_IMAGE_PATH, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""


def render_floating_ai_widget() -> None:
    """Renders a clean floating AI Assistant icon without cyclic borders."""
    img_b64 = _get_ai_icon_base64()
    if not img_b64:
        return

    st.markdown(f"""
    <style>
    @keyframes ag-bulb-glow {{
        0%, 100% {{
            filter: drop-shadow(0 0 5px rgba(255, 240, 160, 0.85))
                    drop-shadow(0 0 12px rgba(74, 222, 128, 0.75))
                    drop-shadow(0 0 24px rgba(34, 197, 94, 0.5))
                    drop-shadow(0 4px 10px rgba(0, 0, 0, 0.25)) !important;
        }}
        50% {{
            filter: drop-shadow(0 0 9px rgba(255, 248, 190, 0.95))
                    drop-shadow(0 0 20px rgba(74, 222, 128, 0.9))
                    drop-shadow(0 0 36px rgba(34, 197, 94, 0.65))
                    drop-shadow(0 6px 14px rgba(0, 0, 0, 0.2)) !important;
        }}
    }}
    @keyframes ag-ambient-light {{
        0%, 100% {{
            opacity: 0.65;
            transform: translate(-50%, -52%) scale(0.95);
        }}
        50% {{
            opacity: 1;
            transform: translate(-50%, -52%) scale(1.15);
        }}
    }}
    .ag-floating-ai-fab {{
        position: fixed !important;
        bottom: 24px !important;
        right: 24px !important;
        z-index: 9999999 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        cursor: pointer !important;
        transition: transform 0.3s cubic-bezier(0.22, 1, 0.36, 1) !important;
        text-decoration: none !important;
    }}
    .ag-floating-ai-fab::before {{
        content: "" !important;
        position: absolute !important;
        top: 50% !important;
        left: 50% !important;
        width: 70px !important;
        height: 100px !important;
        transform: translate(-50%, -52%) !important;
        background: radial-gradient(ellipse at 50% 40%, rgba(255, 245, 180, 0.45) 0%, rgba(74, 222, 128, 0.4) 35%, rgba(34, 197, 94, 0.2) 60%, rgba(16, 185, 129, 0) 80%) !important;
        border-radius: 50% !important;
        filter: blur(12px) !important;
        pointer-events: none !important;
        z-index: -1 !important;
        animation: ag-ambient-light 2.8s ease-in-out infinite alternate !important;
        transition: all 0.3s ease !important;
    }}
    .ag-floating-ai-fab:hover {{
        transform: translateY(-5px) scale(1.08) !important;
    }}
    .ag-floating-ai-fab:hover::before {{
        opacity: 1 !important;
        transform: translate(-50%, -52%) scale(1.25) !important;
        filter: blur(16px) !important;
    }}
    .ag-floating-ai-fab img {{
        width: 58px !important;
        height: auto !important;
        max-height: 92px !important;
        object-fit: contain !important;
        animation: ag-bulb-glow 2.8s ease-in-out infinite !important;
        transition: transform 0.3s ease !important;
    }}
    .ag-floating-ai-fab:hover img {{
        animation: none !important;
        filter: drop-shadow(0 0 12px rgba(255, 252, 200, 1))
                drop-shadow(0 0 26px rgba(74, 222, 128, 0.95))
                drop-shadow(0 0 48px rgba(34, 197, 94, 0.75))
                drop-shadow(0 8px 18px rgba(0, 0, 0, 0.25)) !important;
    }}
    .ag-floating-ai-tooltip {{
        position: absolute !important;
        right: 72px !important;
        background: linear-gradient(
            135deg,
            rgba(255, 255, 255, 0.72) 0%,
            rgba(255, 255, 255, 0.28) 35%,
            rgba(220, 252, 231, 0.38) 70%,
            rgba(187, 247, 208, 0.5) 100%
        ) !important;
        backdrop-filter: blur(16px) saturate(190%) !important;
        -webkit-backdrop-filter: blur(16px) saturate(190%) !important;
        color: #113824 !important;
        font-size: 0.84rem !important;
        font-weight: 700 !important;
        padding: 7px 18px !important;
        border-radius: 9999px !important;
        white-space: nowrap !important;
        pointer-events: none !important;
        opacity: 0 !important;
        transform: translateX(12px) scale(0.96) !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
        border: 1px solid rgba(255, 255, 255, 0.75) !important;
        border-top: 1.5px solid rgba(255, 255, 255, 0.95) !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.45) !important;
        box-shadow:
            0 10px 30px rgba(16, 55, 35, 0.12),
            0 2px 8px rgba(0, 0, 0, 0.04),
            inset 0 1.5px 2px rgba(255, 255, 255, 1),
            inset 0 -1.5px 2px rgba(180, 230, 200, 0.35),
            inset 0 0 14px rgba(255, 255, 255, 0.5) !important;
        text-shadow: 0 1px 1px rgba(255, 255, 255, 0.9) !important;
        letter-spacing: 0.02em !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        overflow: hidden !important;
        display: flex !important;
        align-items: center !important;
        gap: 6px !important;
    }}
    .ag-glass-spark {{
        color: #1b8a5a !important;
        font-size: 0.85rem !important;
        text-shadow: 0 0 6px rgba(45, 180, 110, 0.5) !important;
        line-height: 1 !important;
    }}
    .ag-floating-ai-tooltip::after {{
        content: "" !important;
        position: absolute !important;
        top: 0 !important;
        left: -120% !important;
        width: 70% !important;
        height: 100% !important;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.75), transparent) !important;
        transform: skewX(-25deg) !important;
        transition: left 0.75s ease !important;
        pointer-events: none !important;
    }}
    .ag-floating-ai-fab:hover .ag-floating-ai-tooltip {{
        opacity: 1 !important;
        transform: translateX(0) scale(1) !important;
    }}
    .ag-floating-ai-fab:hover .ag-floating-ai-tooltip::after {{
        left: 150% !important;
    }}
    @media (max-width: 600px) {{
        .ag-floating-ai-fab {{
            bottom: 16px !important;
            right: 16px !important;
        }}
        .ag-floating-ai-fab img {{
            width: 48px !important;
            max-height: 76px !important;
        }}
        .ag-floating-ai-fab::before {{
            width: 58px !important;
            height: 84px !important;
        }}
        .ag-floating-ai-tooltip {{
            right: 60px !important;
            padding: 6px 14px !important;
            font-size: 0.78rem !important;
        }}
    }}
    </style>
    <a href="/AI_Assistant" target="_self" class="ag-floating-ai-fab" aria-label="Ask AI Assistant">
        <img src="data:image/png;base64,{img_b64}" alt="AI Assistant" />
        <div class="ag-floating-ai-tooltip"><span class="ag-glass-spark"><svg width="11" height="11" viewBox="0 0 24 24" fill="#1b8a5a"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg></span> Ask AI Assistant</div>
    </a>
    """, unsafe_allow_html=True)
