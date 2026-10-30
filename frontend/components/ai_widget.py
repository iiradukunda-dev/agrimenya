"""Floating AI Assistant widget visible across all pages."""
import base64
import os
import streamlit as st
import streamlit.components.v1 as components
from utils.i18n import t

_ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
_IMAGE_PATH = os.path.join(_ASSETS_DIR, "ai_assistant_bulb.png")


@st.cache_data
def _get_ai_icon_base64() -> str:
    """Return base64 encoded string of the AI Assistant lightbulb icon."""
    candidates = [
        _IMAGE_PATH,
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "ai_assistant_bulb.png"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "assets", "ai_assistant_bulb.png"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "static", "ai_assistant_bulb.png"),
        "/app/static/ai_assistant_bulb.png",
        "/app/frontend/assets/ai_assistant_bulb.png",
        "/app/assets/ai_assistant_bulb.png",
    ]
    for p in candidates:
        if p and os.path.exists(p):
            try:
                with open(p, "rb") as f:
                    return base64.b64encode(f.read()).decode("utf-8")
            except Exception:
                continue
    return ""


def render_floating_ai_widget() -> None:
    """Renders a persistent, static floating AI Assistant bulb in the bottom right corner.

    The bulb has no glow or continuous pulsing animations and is anchored persistently
    to the top-level window body so that on page
    reload, refresh, or navigation it always stays in place without flickering or restarting animations.
    """
    img_b64 = _get_ai_icon_base64()
    ask_ai_text = t("ai.ask_ai", "Ask AI")

    if img_b64:
        icon_html = f'<img src="data:image/png;base64,{img_b64}" alt="AI Assistant" />'
        js_img_markup = f'<img src="data:image/png;base64,{img_b64}" alt="AI Assistant" />'
    else:
        svg_icon = '<svg width="44" height="60" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/></svg>'
        icon_html = svg_icon
        js_img_markup = svg_icon

    css_rules = """
    .ag-floating-ai-fab {
        position: fixed !important;
        bottom: 24px !important;
        right: 24px !important;
        width: 72px !important;
        height: 104px !important;
        z-index: 9999999 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        cursor: pointer !important;
        animation: none !important;
        transition: transform 0.25s cubic-bezier(0.22, 1, 0.36, 1) !important;
        text-decoration: none !important;
    }
    .ag-floating-ai-fab::before {
        display: none !important;
    }
    .ag-floating-ai-fab:hover {
        transform: translateY(-4px) scale(1.05) !important;
    }
    .ag-floating-ai-fab:hover::before {
        opacity: 1 !important;
        transform: translate(-50%, -52%) scale(1.15) !important;
        filter: blur(14px) !important;
    }
    .ag-floating-ai-fab img {
        width: 58px !important;
        height: auto !important;
        max-height: 92px !important;
        object-fit: contain !important;
        animation: none !important;
        filter: none !important;
        transition: transform 0.25s ease !important;
    }
    .ag-floating-ai-fab:hover img {
        animation: none !important;
        filter: none !important;
    }
    .ag-floating-ai-tooltip {
        position: absolute !important;
        right: 76px !important;
        top: 50% !important;
        transform: translateY(-50%) translateX(12px) scale(0.96) !important;
        background: #ffffff !important;
        color: #0284c7 !important;
        font-size: 0.86rem !important;
        font-weight: 750 !important;
        padding: 8px 18px !important;
        border-radius: 9999px !important;
        white-space: nowrap !important;
        pointer-events: none !important;
        opacity: 0 !important;
        visibility: hidden !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
        border: 1px solid rgba(2, 132, 199, 0.22) !important;
        box-shadow: 0 10px 30px rgba(2, 132, 199, 0.16) !important;
        letter-spacing: 0.02em !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        overflow: hidden !important;
        display: flex !important;
        align-items: center !important;
        gap: 6px !important;
        z-index: 10000000 !important;
    }
    .ag-floating-ai-fab:hover .ag-floating-ai-tooltip,
    .ag-floating-ai-fab:focus .ag-floating-ai-tooltip,
    .ag-floating-ai-fab:active .ag-floating-ai-tooltip {
        opacity: 1 !important;
        visibility: visible !important;
        transform: translateY(-50%) translateX(0) scale(1) !important;
    }
    @media (max-width: 600px) {
        .ag-floating-ai-fab {
            bottom: 12px !important;
            right: 12px !important;
            width: 48px !important;
            height: 48px !important;
            border-radius: 50% !important;
            background: rgba(255, 255, 255, 0.96) !important;
            box-shadow: 0 4px 16px rgba(2, 132, 199, 0.24) !important;
        }
        .ag-floating-ai-fab img {
            width: 34px !important;
            height: 42px !important;
            max-height: 42px !important;
        }
        .ag-floating-ai-fab::before {
            width: 48px !important;
            height: 48px !important;
        }
        .ag-floating-ai-tooltip {
            right: 54px !important;
            padding: 6px 14px !important;
            font-size: 0.78rem !important;
        }
    }
    """

    st.markdown(f"""
    <style>
    {css_rules}
    </style>
    <a id="ag-persistent-ai-fab" class="ag-floating-ai-fab" href="/AI_Assistant" target="_self" aria-label="{ask_ai_text}" title="{ask_ai_text}">
        {icon_html}
        <div class="ag-floating-ai-tooltip">
            {ask_ai_text}
        </div>
    </a>
    <script>
    (function ensurePersistentAiBulb() {{
        try {{
            const parentDoc = window.parent.document || document;
            if (!parentDoc) return;
            function wireFabClick(element) {{
                if (!element || element.__ag_fab_click_attached) return;
                element.__ag_fab_click_attached = true;
                element.addEventListener('click', function(e) {{
                    e.preventDefault();
                    window.parent.location.href = '/AI_Assistant';
                }});
            }}
            let fab = parentDoc.getElementById('ag-persistent-ai-fab');
            if (fab) {{
                fab.target = '_self';
                wireFabClick(fab);
            }}
        }} catch(e) {{}}
    }})();
    </script>
    """, unsafe_allow_html=True)

    # Use components.html iframe execution to guarantee DOM persistence and attachment to parent document body
    js_script = f"""
    <script>
    (function ensurePersistentAiBulb() {{
        try {{
            const parentDoc = window.parent.document || document;
            if (!parentDoc) return;

            // Ensure styles are injected into parent document head
            if (!parentDoc.getElementById('ag-persistent-ai-fab-style')) {{
                const styleEl = parentDoc.createElement('style');
                styleEl.id = 'ag-persistent-ai-fab-style';
                styleEl.textContent = `{css_rules}`;
                parentDoc.head.appendChild(styleEl);
            }}

            // Function to attach click handler
            function wireFabClick(element) {{
                if (!element || element.__ag_fab_click_attached) return;
                element.__ag_fab_click_attached = true;
                element.addEventListener('click', function(e) {{
                    e.preventDefault();
                    const currentPath = (window.parent.location.pathname || '') + (window.parent.location.search || '');
                    if (currentPath.toLowerCase().includes('ai_assistant') || currentPath.toLowerCase().includes('7_ai_assistant')) {{
                        window.parent.scrollTo({{ top: 0, behavior: 'smooth' }});
                        return;
                    }}
                    const internalLink = parentDoc.querySelector('a[href*="AI_Assistant"], a[href*="7_AI_Assistant"], [data-testid="stPageLink"] a[href*="Assistant"]');
                    if (internalLink) {{
                        internalLink.click();
                    }} else {{
                        window.parent.location.href = '/AI_Assistant';
                    }}
                }});
            }}

            let fab = parentDoc.getElementById('ag-persistent-ai-fab');
            if (!fab) {{
                fab = parentDoc.createElement('a');
                fab.id = 'ag-persistent-ai-fab';
                fab.href = '/AI_Assistant';
                fab.target = '_self';
                fab.className = 'ag-floating-ai-fab';
                fab.setAttribute('aria-label', '{ask_ai_text}');
                fab.setAttribute('title', '{ask_ai_text}');
                fab.innerHTML = `
                    {js_img_markup}
                    <div class="ag-floating-ai-tooltip">
                        {ask_ai_text}
                    </div>
                `;
                parentDoc.body.appendChild(fab);
            }} else {{
                if (!parentDoc.body.contains(fab)) {{
                    parentDoc.body.appendChild(fab);
                }}
                fab.style.display = 'flex';
                fab.target = '_self';
                fab.setAttribute('aria-label', '{ask_ai_text}');
                fab.setAttribute('title', '{ask_ai_text}');
                const tt = fab.querySelector('.ag-floating-ai-tooltip');
                if (tt) {{
                    tt.textContent = '{ask_ai_text}';
                }}
            }}
            wireFabClick(fab);
        }} catch(e) {{
            console.debug('Persistent AI bulb note:', e);
        }}
    }})();
    </script>
    """
    components.html(js_script, height=0)
