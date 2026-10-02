"""
Design system for agrimenya — a premium agriculture and climate intelligence platform.

Inspired by:
- Apple visionOS Liquid Glass translucency and depth
- Modern agtech dashboard clarity (Phenomenon Studio, f1Studioz)
- Nature-forward color palette grounded in Rwandan landscapes
"""
import streamlit as st


def load_theme() -> None:
    """
    Injects the complete agrimenya design system into the Streamlit page.

    This includes:
    - Google Fonts (Inter + Space Grotesk)
    - CSS custom properties (design tokens)
    - Ambient background layer (animated gradient orbs)
    - Glassmorphism surfaces for cards, metrics, inputs, tabs, etc.
    - Plotly / dataframe harmonisation
    - PWA manifest and service-worker registration
    """

    # ── PWA registration ──────────────────────────────────────────────
    st.html("""
    <script>
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/app/static/sw.js')
            .then(function(reg) { console.log('SW scope:', reg.scope); })
            .catch(function(err) { console.error('SW fail:', err); });
        }
        if (!document.querySelector('link[rel="manifest"]')) {
            var l = document.createElement('link');
            l.rel = 'manifest'; l.href = '/app/static/manifest.json';
            document.head.appendChild(l);
        }
        if (!document.querySelector('meta[name="theme-color"]')) {
            var m = document.createElement('meta');
            m.name = 'theme-color'; m.content = '#1B3A2D';
            document.head.appendChild(m);
        }
    </script>
    """, unsafe_allow_javascript=True)

    # ── Design system CSS + ambient background ────────────────────────
    st.html("""
    <style>
    /* ═══════════════════════════════════════════════════════════════
       AGRIMENYA DESIGN SYSTEM v2.0
       Premium agriculture & climate intelligence platform
       ═══════════════════════════════════════════════════════════════ */

    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700;800&display=swap');

    /* ── Design Tokens ─────────────────────────────────────────── */
    :root {
        /* Primary — deep forest greens */
        --ag-forest-900: #0B1F14;
        --ag-forest-800: #1B3A2D;
        --ag-forest-700: #2D6A4F;
        --ag-forest-600: #40916C;
        --ag-forest-500: #52B788;
        --ag-forest-400: #74C69D;
        --ag-forest-300: #95D5B2;
        --ag-forest-200: #B7E4C7;
        --ag-forest-100: #D8F3DC;
        --ag-forest-050: #EDF7F0;

        /* Accent — warm earth tones */
        --ag-earth-700: #7C4A1E;
        --ag-earth-600: #A16027;
        --ag-earth-500: #C4924A;
        --ag-earth-400: #D4A96A;
        --ag-earth-300: #E4C68E;
        --ag-earth-100: #FDF4E8;

        /* Neutral */
        --ag-neutral-900: #111827;
        --ag-neutral-800: #1F2937;
        --ag-neutral-700: #374151;
        --ag-neutral-600: #4B5563;
        --ag-neutral-500: #6B7280;
        --ag-neutral-400: #9CA3AF;
        --ag-neutral-300: #D1D5DB;
        --ag-neutral-200: #E5E7EB;
        --ag-neutral-100: #F3F4F6;
        --ag-neutral-050: #F9FAFB;

        /* Semantic */
        --ag-danger:  #DC2626;
        --ag-warning: #D97706;
        --ag-success: #059669;
        --ag-info:    #2563EB;

        /* Glass surfaces */
        --ag-glass-fill: linear-gradient(
            135deg,
            rgba(255, 255, 255, 0.50) 0%,
            rgba(255, 255, 255, 0.18) 100%
        );
        --ag-glass-border: rgba(255, 255, 255, 0.45);
        --ag-glass-blur: blur(28px) saturate(180%) brightness(1.05);
        --ag-glass-shadow:
            0 4px 6px  rgba(0, 0, 0, 0.04),
            0 10px 30px rgba(0, 0, 0, 0.08);
        --ag-glass-highlight:
            inset 0 1px 0 rgba(255, 255, 255, 0.7),
            inset 0 -1px 0 rgba(255, 255, 255, 0.15);

        /* Typography */
        --ag-font-body:    'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        --ag-font-display: 'Space Grotesk', var(--ag-font-body);

        /* Radius */
        --ag-radius-sm:   8px;
        --ag-radius-md:   16px;
        --ag-radius-lg:   24px;
        --ag-radius-pill: 50px;

        /* Motion */
        --ag-ease: cubic-bezier(0.22, 1, 0.36, 1);
    }

    /* ── Global Reset & Typography ────────────────────────────── */
    html, body, [class*="css"], .stApp {
        font-family: var(--ag-font-body) !important;
        color: var(--ag-neutral-800);
        background: transparent !important;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
    h1, h2, h3 {
        font-family: var(--ag-font-display) !important;
        color: var(--ag-forest-800) !important;
        letter-spacing: -0.02em;
    }
    h1 { font-weight: 800 !important; }
    h2 { font-weight: 700 !important; }
    h3 { font-weight: 600 !important; }

    p, li, span, label {
        line-height: 1.65;
        color: var(--ag-neutral-700);
    }

    /* ── Hide Streamlit Chrome ────────────────────────────────── */
    #MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }

    /* ── Ambient Background ───────────────────────────────────── */
    .ag-ambient {
        position: fixed;
        inset: 0;
        z-index: -1;
        overflow: hidden;
        background: linear-gradient(160deg, #F0F7F2 0%, #EDF5ED 40%, #F5F0E8 100%);
    }
    .ag-orb {
        position: absolute;
        border-radius: 50%;
        filter: blur(100px);
        opacity: 0.45;
        animation: orbFloat 30s infinite alternate ease-in-out;
        will-change: transform;
    }
    .ag-orb-1 { width: 650px; height: 650px; background: var(--ag-forest-400); top: -15%; left: -10%; }
    .ag-orb-2 { width: 550px; height: 550px; background: var(--ag-earth-300);  bottom: -12%; right: -8%; animation-delay: -7s; }
    .ag-orb-3 { width: 700px; height: 700px; background: var(--ag-forest-200); top: 35%; left: 45%; animation-delay: -14s; }
    .ag-orb-4 { width: 400px; height: 400px; background: var(--ag-earth-400);  top: 10%; right: 20%; animation-delay: -20s; opacity: 0.25; }

    @keyframes orbFloat {
        0%   { transform: translate(0, 0) scale(1); }
        33%  { transform: translate(60px, 30px) scale(1.08); }
        66%  { transform: translate(-40px, 60px) scale(0.95); }
        100% { transform: translate(30px, -20px) scale(1.03); }
    }

    /* ── Content Entrance Animation ───────────────────────────── */
    @keyframes slideUp {
        from { opacity: 0; transform: translateY(24px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    .block-container {
        padding-top: 2rem !important;
        animation: slideUp 0.6s var(--ag-ease) forwards;
    }

    /* ── Metric Cards — Glass Surface ─────────────────────────── */
    [data-testid="stMetric"] {
        background: var(--ag-glass-fill);
        backdrop-filter: var(--ag-glass-blur);
        -webkit-backdrop-filter: var(--ag-glass-blur);
        border: 1px solid var(--ag-glass-border);
        border-radius: var(--ag-radius-lg);
        padding: 28px 24px;
        box-shadow: var(--ag-glass-shadow), var(--ag-glass-highlight);
        transition: all 0.4s var(--ag-ease);
        animation: slideUp 0.7s var(--ag-ease) backwards;
    }
    [data-testid="stMetric"]:nth-child(1) { animation-delay: 0.1s; }
    [data-testid="stMetric"]:nth-child(2) { animation-delay: 0.2s; }
    [data-testid="stMetric"]:nth-child(3) { animation-delay: 0.3s; }
    [data-testid="stMetric"]:hover {
        transform: translateY(-6px) scale(1.01);
        box-shadow:
            0 20px 40px rgba(45, 106, 79, 0.12),
            0 8px 16px rgba(45, 106, 79, 0.08),
            var(--ag-glass-highlight);
    }
    [data-testid="stMetricLabel"] {
        font-family: var(--ag-font-body) !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--ag-neutral-500) !important;
    }
    [data-testid="stMetricValue"] {
        font-family: var(--ag-font-display) !important;
        font-weight: 800 !important;
        font-size: 2rem !important;
        color: var(--ag-forest-800) !important;
        line-height: 1.2;
    }
    [data-testid="stMetricDelta"] {
        font-weight: 600 !important;
        font-size: 0.85rem !important;
    }

    /* ── Buttons ──────────────────────────────────────────────── */
    .stButton > button {
        background: var(--ag-glass-fill) !important;
        backdrop-filter: var(--ag-glass-blur);
        -webkit-backdrop-filter: var(--ag-glass-blur);
        border: 1px solid var(--ag-glass-border) !important;
        border-radius: var(--ag-radius-pill) !important;
        box-shadow: var(--ag-glass-shadow), var(--ag-glass-highlight);
        color: var(--ag-forest-800) !important;
        font-weight: 600 !important;
        font-family: var(--ag-font-body) !important;
        padding: 0.55rem 1.5rem !important;
        transition: all 0.3s var(--ag-ease) !important;
        position: relative;
        overflow: hidden;
    }
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0; left: -100%;
        width: 60%; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.7), transparent);
        transform: skewX(-20deg);
        transition: left 0.6s var(--ag-ease);
    }
    .stButton > button:hover::before { left: 200%; }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 12px 28px rgba(45, 106, 79, 0.15), var(--ag-glass-highlight) !important;
        border-color: var(--ag-forest-400) !important;
    }
    .stButton > button:active {
        transform: scale(0.97) !important;
    }

    /* Primary button — solid gradient */
    button[kind="primary"], .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--ag-forest-500), var(--ag-forest-700)) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255,255,255,0.25) !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, var(--ag-forest-400), var(--ag-forest-600)) !important;
        box-shadow: 0 12px 28px rgba(82, 183, 136, 0.3), var(--ag-glass-highlight) !important;
    }

    /* ── Text Inputs, Selects, Textareas ──────────────────────── */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div,
    .stMultiSelect > div > div > div,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input {
        background: rgba(255, 255, 255, 0.45) !important;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(209, 213, 219, 0.6) !important;
        border-radius: var(--ag-radius-sm) !important;
        color: var(--ag-neutral-800) !important;
        font-family: var(--ag-font-body) !important;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.03) !important;
        transition: all 0.3s var(--ag-ease) !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > div:focus-within {
        background: rgba(255, 255, 255, 0.7) !important;
        border-color: var(--ag-forest-500) !important;
        box-shadow: 0 0 0 3px rgba(82, 183, 136, 0.15), inset 0 2px 4px rgba(0,0,0,0.03) !important;
    }

    /* ── Tabs — Pill-style segmented control ───────────────────── */
    [data-baseweb="tab-list"] {
        background: rgba(255, 255, 255, 0.3);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: var(--ag-radius-pill);
        padding: 5px;
        border: 1px solid var(--ag-glass-border);
        gap: 4px;
    }
    [data-baseweb="tab"] {
        border-radius: var(--ag-radius-pill) !important;
        font-family: var(--ag-font-body) !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        transition: all 0.3s var(--ag-ease) !important;
        padding: 8px 20px !important;
    }
    [aria-selected="true"] {
        background: #ffffff !important;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08) !important;
        color: var(--ag-forest-700) !important;
        font-weight: 600 !important;
    }

    /* ── Containers with border ────────────────────────────────── */
    [data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--ag-glass-fill) !important;
        backdrop-filter: blur(20px) saturate(160%);
        -webkit-backdrop-filter: blur(20px) saturate(160%);
        border: 1px solid var(--ag-glass-border) !important;
        border-radius: var(--ag-radius-md) !important;
        box-shadow: var(--ag-glass-shadow);
        transition: all 0.3s var(--ag-ease);
    }
    [data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        box-shadow: 0 8px 25px rgba(45, 106, 79, 0.1);
    }

    /* ── Chat Messages ────────────────────────────────────────── */
    [data-testid="stChatMessage"] {
        background: var(--ag-glass-fill) !important;
        backdrop-filter: var(--ag-glass-blur);
        -webkit-backdrop-filter: var(--ag-glass-blur);
        border: 1px solid var(--ag-glass-border);
        border-radius: var(--ag-radius-md);
        padding: 1rem;
        box-shadow: var(--ag-glass-shadow);
        margin-bottom: 0.75rem;
    }

    /* ── Sidebar Glass (when visible) ─────────────────────────── */
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.25) !important;
        backdrop-filter: blur(30px) saturate(180%);
        -webkit-backdrop-filter: blur(30px) saturate(180%);
        border-right: 1px solid var(--ag-glass-border);
    }

    /* ── Checkboxes ───────────────────────────────────────────── */
    .stCheckbox label span[data-baseweb="checkbox"] {
        border-color: var(--ag-forest-400) !important;
    }
    .stCheckbox label span[data-baseweb="checkbox"][aria-checked="true"] {
        background-color: var(--ag-forest-500) !important;
        border-color: var(--ag-forest-500) !important;
    }

    /* ── Dataframes ───────────────────────────────────────────── */
    [data-testid="stDataFrame"] {
        border-radius: var(--ag-radius-md) !important;
        overflow: hidden;
    }

    /* ── Dividers — gradient fade ─────────────────────────────── */
    hr {
        margin: 2.5rem 0 !important;
        border: 0 !important;
        height: 1px !important;
        background: linear-gradient(
            to right,
            transparent 0%,
            var(--ag-forest-300) 30%,
            var(--ag-forest-500) 50%,
            var(--ag-forest-300) 70%,
            transparent 100%
        ) !important;
        opacity: 0.4;
    }

    /* ── Pillar / Feature Cards ───────────────────────────────── */
    .ag-card {
        background: var(--ag-glass-fill);
        backdrop-filter: var(--ag-glass-blur);
        -webkit-backdrop-filter: var(--ag-glass-blur);
        border: 1px solid var(--ag-glass-border);
        border-radius: var(--ag-radius-lg);
        padding: 32px 28px;
        box-shadow: var(--ag-glass-shadow), var(--ag-glass-highlight);
        transition: all 0.4s var(--ag-ease);
        position: relative;
        overflow: hidden;
        height: 100%;
    }
    .ag-card::before {
        content: '';
        position: absolute;
        top: 0; left: -120%;
        width: 60%; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent);
        transform: skewX(-25deg);
        transition: left 0.7s var(--ag-ease);
    }
    .ag-card:hover::before { left: 200%; }
    .ag-card:hover {
        transform: translateY(-6px);
        box-shadow:
            0 20px 40px rgba(45, 106, 79, 0.12),
            0 8px 16px rgba(45, 106, 79, 0.06),
            var(--ag-glass-highlight);
        border-color: var(--ag-forest-400);
    }

    .ag-card-icon {
        width: 52px; height: 52px;
        border-radius: 14px;
        background: linear-gradient(135deg, var(--ag-forest-050), var(--ag-forest-100));
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(82, 183, 136, 0.15);
    }
    .ag-card-icon svg {
        width: 26px; height: 26px;
        color: var(--ag-forest-600);
    }

    .ag-card-title {
        font-family: var(--ag-font-display);
        font-size: 1.2rem;
        font-weight: 700;
        color: var(--ag-forest-800);
        margin-bottom: 10px;
        line-height: 1.3;
    }
    .ag-card-desc {
        font-size: 0.92rem;
        color: var(--ag-neutral-600);
        line-height: 1.65;
    }

    /* ── Alert / Notification Cards ───────────────────────────── */
    .ag-alert {
        border-radius: var(--ag-radius-md);
        padding: 18px 20px;
        margin-bottom: 12px;
        display: flex;
        align-items: flex-start;
        gap: 14px;
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        transition: all 0.3s var(--ag-ease);
        animation: slideUp 0.5s var(--ag-ease) backwards;
    }
    .ag-alert:hover {
        transform: translateX(4px);
    }
    .ag-alert-info {
        background: rgba(237, 247, 240, 0.85);
        border: 1px solid rgba(149, 213, 178, 0.5);
        border-left: 4px solid var(--ag-forest-500);
    }
    .ag-alert-warning {
        background: rgba(253, 244, 232, 0.85);
        border: 1px solid rgba(252, 211, 77, 0.5);
        border-left: 4px solid var(--ag-warning);
    }
    .ag-alert-urgent {
        background: rgba(254, 242, 242, 0.85);
        border: 1px solid rgba(252, 165, 165, 0.5);
        border-left: 4px solid var(--ag-danger);
    }

    /* ── Priority Badges ──────────────────────────────────────── */
    .ag-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 14px;
        border-radius: var(--ag-radius-pill);
        font-weight: 600;
        font-size: 0.8rem;
        font-family: var(--ag-font-body);
        letter-spacing: 0.02em;
        backdrop-filter: blur(6px);
    }
    .ag-badge::before {
        content: '';
        width: 7px; height: 7px;
        border-radius: 50%;
        display: inline-block;
    }
    .ag-badge-high {
        background: rgba(254, 226, 226, 0.8);
        color: #991B1B;
        border: 1px solid rgba(252, 165, 165, 0.6);
    }
    .ag-badge-high::before { background: #DC2626; }
    .ag-badge-medium {
        background: rgba(254, 243, 199, 0.8);
        color: #92400E;
        border: 1px solid rgba(252, 211, 77, 0.6);
    }
    .ag-badge-medium::before { background: #D97706; }
    .ag-badge-low {
        background: rgba(216, 243, 220, 0.8);
        color: #1B4332;
        border: 1px solid rgba(149, 213, 178, 0.6);
    }
    .ag-badge-low::before { background: #059669; }

    /* ── Error Page ───────────────────────────────────────────── */
    .ag-error-container {
        background: var(--ag-glass-fill);
        backdrop-filter: var(--ag-glass-blur);
        -webkit-backdrop-filter: var(--ag-glass-blur);
        border: 1px solid var(--ag-glass-border);
        border-radius: var(--ag-radius-lg);
        padding: 48px 40px;
        text-align: center;
        box-shadow: var(--ag-glass-shadow), var(--ag-glass-highlight);
        margin: 48px auto;
        max-width: 560px;
    }
    .ag-error-container h2 {
        color: var(--ag-forest-800) !important;
        font-size: 1.8rem;
        margin-bottom: 12px;
    }
    .ag-error-container p {
        color: var(--ag-neutral-600);
        font-size: 1.05rem;
        line-height: 1.6;
    }
    .ag-error-details {
        text-align: left;
        font-family: 'SF Mono', 'Fira Code', monospace;
        background: rgba(243, 244, 246, 0.6);
        padding: 14px;
        border-radius: var(--ag-radius-sm);
        font-size: 0.85rem;
        border: 1px solid var(--ag-neutral-200);
        overflow-x: auto;
        margin: 16px 0 24px;
        color: var(--ag-neutral-700);
    }

    /* ── Page Link Navbar Styling ──────────────────────────────── */
    div[data-testid="stPageLink-NavLink"] {
        background: rgba(255, 255, 255, 0.5);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(209, 213, 219, 0.4);
        border-radius: var(--ag-radius-sm);
        padding: 8px 14px;
        transition: all 0.25s var(--ag-ease);
        text-align: center;
    }
    div[data-testid="stPageLink-NavLink"]:hover {
        background: var(--ag-forest-050);
        border-color: var(--ag-forest-300);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(82, 183, 136, 0.1);
    }
    div[data-testid="stPageLink-NavLink"][aria-current="page"],
    div[data-testid="stPageLink-NavLink"][data-active="true"] {
        background: linear-gradient(135deg, var(--ag-forest-500), var(--ag-forest-700)) !important;
        border-color: var(--ag-forest-500) !important;
        box-shadow: 0 4px 14px rgba(82, 183, 136, 0.25);
    }
    div[data-testid="stPageLink-NavLink"][aria-current="page"] p,
    div[data-testid="stPageLink-NavLink"][data-active="true"] p {
        color: #ffffff !important;
        font-weight: 600;
    }

    /* ── Plotly Chart Containers ───────────────────────────────── */
    [data-testid="stPlotlyChart"] {
        border-radius: var(--ag-radius-md);
        overflow: hidden;
    }

    /* ── Expanders ─────────────────────────────────────────────── */
    [data-testid="stExpander"] {
        background: rgba(255, 255, 255, 0.3);
        backdrop-filter: blur(10px);
        border: 1px solid var(--ag-glass-border);
        border-radius: var(--ag-radius-md) !important;
    }

    /* ── Captions & Fine Print ─────────────────────────────────── */
    .stCaption, [data-testid="stCaptionContainer"] {
        color: var(--ag-neutral-400) !important;
        font-size: 0.82rem !important;
    }

    /* ── Success / Error / Warning / Info Alerts ───────────────── */
    [data-testid="stAlert"] {
        border-radius: var(--ag-radius-sm) !important;
        backdrop-filter: blur(6px);
    }

    /* ── Scrollbar Styling ─────────────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: var(--ag-forest-300);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover { background: var(--ag-forest-400); }

    /* ── Forms ─────────────────────────────────────────────────── */
    [data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.25) !important;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid var(--ag-glass-border) !important;
        border-radius: var(--ag-radius-md) !important;
        padding: 24px !important;
    }

    /* Legacy card class — kept for backward compat */
    .custom-card { /* mapped to .ag-card */ }
    .custom-card-title { /* mapped to .ag-card-title */ }
    .custom-card-desc { /* mapped to .ag-card-desc */ }

    </style>

    <!-- Ambient Background Orbs -->
    <div class="ag-ambient">
        <div class="ag-orb ag-orb-1"></div>
        <div class="ag-orb ag-orb-2"></div>
        <div class="ag-orb ag-orb-3"></div>
        <div class="ag-orb ag-orb-4"></div>
    </div>
    """, unsafe_allow_javascript=True)
