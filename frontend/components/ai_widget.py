"""Floating AI Assistant widget visible across all pages."""
import base64
import os
import streamlit as st
from utils.i18n import t

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
    """Renders a persistent, static floating AI Assistant bulb in the bottom right corner.

    The bulb has a steady, clean bio-luminescent glow with zero continuous pulsing
    animations and is anchored persistently to the top-level window body so that on page
    reload, refresh, or navigation it always stays in place without flickering or restarting animations.
    """
    img_b64 = _get_ai_icon_base64()
    if not img_b64:
        return

    ask_ai_text = t("ai.ask_ai", "Ask AI")

    st.markdown(f"""
    <style>
    /* Static, steady glow without continuous pulsing animations */
    .ag-floating-ai-fab {{
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
    }}
    .ag-floating-ai-fab::before {{
        content: "" !important;
        position: absolute !important;
        top: 50% !important;
        left: 50% !important;
        width: 70px !important;
        height: 100px !important;
        transform: translate(-50%, -52%) !important;
        background: radial-gradient(ellipse at 50% 40%, rgba(56, 189, 248, 0.4) 0%, rgba(14, 165, 233, 0.18) 45%, transparent 75%) !important;
        border-radius: 50% !important;
        filter: blur(12px) !important;
        pointer-events: none !important;
        z-index: -1 !important;
        animation: none !important;
        opacity: 0.85 !important;
        transition: opacity 0.25s ease, transform 0.25s ease !important;
    }}
    .ag-floating-ai-fab:hover {{
        transform: translateY(-4px) scale(1.05) !important;
    }}
    .ag-floating-ai-fab:hover::before {{
        opacity: 1 !important;
        transform: translate(-50%, -52%) scale(1.15) !important;
        filter: blur(14px) !important;
    }}
    .ag-floating-ai-fab img {{
        width: 58px !important;
        height: auto !important;
        max-height: 92px !important;
        object-fit: contain !important;
        animation: none !important;
        filter: drop-shadow(0 0 8px rgba(56, 189, 248, 0.75))
                drop-shadow(0 4px 12px rgba(0, 0, 0, 0.3)) !important;
        transition: filter 0.25s ease, transform 0.25s ease !important;
    }}
    .ag-floating-ai-fab:hover img {{
        animation: none !important;
        filter: drop-shadow(0 0 16px rgba(56, 189, 248, 0.9))
                drop-shadow(0 6px 14px rgba(0, 0, 0, 0.35)) !important;
    }}
    .ag-floating-ai-tooltip {{
        position: absolute !important;
        right: 76px !important;
        top: 50% !important;
        transform: translateY(-50%) translateX(12px) scale(0.96) !important;
        background: #041622 !important;
        color: #ffffff !important;
        font-size: 0.86rem !important;
        font-weight: 750 !important;
        padding: 8px 18px !important;
        border-radius: 9999px !important;
        white-space: nowrap !important;
        pointer-events: none !important;
        opacity: 0 !important;
        visibility: hidden !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
        border: 1px solid rgba(56, 189, 248, 0.6) !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45) !important;
        letter-spacing: 0.02em !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        overflow: hidden !important;
        display: flex !important;
        align-items: center !important;
        gap: 6px !important;
        z-index: 10000000 !important;
    }}
    .ag-ai-spark {{
        color: #38bdf8 !important;
        display: flex !important;
        align-items: center !important;
        line-height: 1 !important;
    }}
    .ag-floating-ai-fab:hover .ag-floating-ai-tooltip,
    .ag-floating-ai-fab:focus .ag-floating-ai-tooltip,
    .ag-floating-ai-fab:active .ag-floating-ai-tooltip {{
        opacity: 1 !important;
        visibility: visible !important;
        transform: translateY(-50%) translateX(0) scale(1) !important;
    }}
    @media (max-width: 600px) {{
        .ag-floating-ai-fab {{
            bottom: 16px !important;
            right: 16px !important;
            width: 58px !important;
            height: 84px !important;
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
            right: 64px !important;
            padding: 6px 14px !important;
            font-size: 0.78rem !important;
        }}
    }}
    </style>
    <script>
    (function ensurePersistentAiBulb() {{
        try {{
            const parentDoc = window.parent.document || document;
            if (!parentDoc) return;

            // Ensure styles are injected into parent document head
            if (!parentDoc.getElementById('ag-persistent-ai-fab-style')) {{
                const styleEl = parentDoc.createElement('style');
                styleEl.id = 'ag-persistent-ai-fab-style';
                styleEl.textContent = `
                .ag-floating-ai-fab {{
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
                }}
                .ag-floating-ai-fab::before {{
                    content: "" !important;
                    position: absolute !important;
                    top: 50% !important;
                    left: 50% !important;
                    width: 70px !important;
                    height: 100px !important;
                    transform: translate(-50%, -52%) !important;
                    background: radial-gradient(ellipse at 50% 40%, rgba(56, 189, 248, 0.4) 0%, rgba(14, 165, 233, 0.18) 45%, transparent 75%) !important;
                    border-radius: 50% !important;
                    filter: blur(12px) !important;
                    pointer-events: none !important;
                    z-index: -1 !important;
                    animation: none !important;
                    opacity: 0.85 !important;
                    transition: opacity 0.25s ease, transform 0.25s ease !important;
                }}
                .ag-floating-ai-fab:hover {{
                    transform: translateY(-4px) scale(1.05) !important;
                }}
                .ag-floating-ai-fab:hover::before {{
                    opacity: 1 !important;
                    transform: translate(-50%, -52%) scale(1.15) !important;
                    filter: blur(14px) !important;
                }}
                .ag-floating-ai-fab img {{
                    width: 58px !important;
                    height: auto !important;
                    max-height: 92px !important;
                    object-fit: contain !important;
                    animation: none !important;
                    filter: drop-shadow(0 0 8px rgba(56, 189, 248, 0.75))
                            drop-shadow(0 4px 12px rgba(0, 0, 0, 0.3)) !important;
                    transition: filter 0.25s ease, transform 0.25s ease !important;
                }}
                .ag-floating-ai-fab:hover img {{
                    animation: none !important;
                    filter: drop-shadow(0 0 16px rgba(56, 189, 248, 0.9))
                            drop-shadow(0 6px 14px rgba(0, 0, 0, 0.35)) !important;
                }}
                .ag-floating-ai-tooltip {{
                    position: absolute !important;
                    right: 76px !important;
                    top: 50% !important;
                    transform: translateY(-50%) translateX(12px) scale(0.96) !important;
                    background: #041622 !important;
                    color: #ffffff !important;
                    font-size: 0.86rem !important;
                    font-weight: 750 !important;
                    padding: 8px 18px !important;
                    border-radius: 9999px !important;
                    white-space: nowrap !important;
                    pointer-events: none !important;
                    opacity: 0 !important;
                    visibility: hidden !important;
                    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
                    border: 1px solid rgba(56, 189, 248, 0.6) !important;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45) !important;
                    letter-spacing: 0.02em !important;
                    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
                    overflow: hidden !important;
                    display: flex !important;
                    align-items: center !important;
                    gap: 6px !important;
                    z-index: 10000000 !important;
                }}
                .ag-ai-spark {{
                    color: #38bdf8 !important;
                    display: flex !important;
                    align-items: center !important;
                    line-height: 1 !important;
                }}
                .ag-floating-ai-fab:hover .ag-floating-ai-tooltip,
                .ag-floating-ai-fab:focus .ag-floating-ai-tooltip,
                .ag-floating-ai-fab:active .ag-floating-ai-tooltip {{
                    opacity: 1 !important;
                    visibility: visible !important;
                    transform: translateY(-50%) translateX(0) scale(1) !important;
                }}
                @media (max-width: 600px) {{
                    .ag-floating-ai-fab {{
                        bottom: 16px !important;
                        right: 16px !important;
                        width: 58px !important;
                        height: 84px !important;
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
                        right: 64px !important;
                        padding: 6px 14px !important;
                        font-size: 0.78rem !important;
                    }}
                }}
                `;
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
                    // Try to trigger Streamlit's internal SPA page navigation if available in DOM
                    const internalLink = parentDoc.querySelector('a[href*="AI_Assistant"], a[href*="7_AI_Assistant"], [data-testid="stPageLink"] a[href*="Assistant"]');
                    if (internalLink) {{
                        internalLink.click();
                    }} else {{
                        // Same-tab navigation
                        window.parent.location.href = '/AI_Assistant';
                    }}
                }});
            }}

            // Check if already anchored on parent document body
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
                    <img src="data:image/png;base64,{img_b64}" alt="AI Assistant" />
                    <div class="ag-floating-ai-tooltip">
                        <span class="ag-ai-spark"><svg width="11" height="11" viewBox="0 0 24 24" fill="#38bdf8"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg></span> {ask_ai_text}
                    </div>
                `;
                parentDoc.body.appendChild(fab);
            }} else {{
                // Ensure it remains in the body and has latest tooltip
                if (!parentDoc.body.contains(fab)) {{
                    parentDoc.body.appendChild(fab);
                }}
                fab.style.display = 'flex';
                fab.target = '_self';
                fab.setAttribute('aria-label', '{ask_ai_text}');
                fab.setAttribute('title', '{ask_ai_text}');
                const tt = fab.querySelector('.ag-floating-ai-tooltip');
                if (tt) {{
                    tt.innerHTML = `<span class="ag-ai-spark"><svg width="11" height="11" viewBox="0 0 24 24" fill="#38bdf8"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg></span> {ask_ai_text}`;
                }}
            }}
            wireFabClick(fab);
        }} catch(e) {{
            console.debug('Persistent AI bulb note:', e);
        }}
    }})();
    </script>
    """, unsafe_allow_html=True)
