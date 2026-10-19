"""Shared visual system for the agrimenya Streamlit application."""
import streamlit as st


def load_theme() -> None:
    """Apply a modern, high-contrast, polished visual system with smooth animations."""
    st.html("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

    :root {
      /* Palette */
      --ag-primary: #10b981;
      --ag-primary-hover: #059669;
      --ag-primary-soft: rgba(16, 185, 129, 0.12);
      --ag-primary-glow: rgba(16, 185, 129, 0.32);

      --ag-forest: #0d3b28;
      --ag-forest-dark: #072418;
      --ag-forest-light: #165338;

      --ag-gold: #f59e0b;
      --ag-gold-soft: rgba(245, 158, 11, 0.12);
      --ag-gold-glow: rgba(245, 158, 11, 0.35);

      --ag-sky: #0ea5e9;
      --ag-sky-soft: rgba(14, 165, 233, 0.12);

      --ag-ink: #11221a;
      --ag-muted: #536b5c;
      --ag-line: #e3eae4;
      --ag-line-glow: rgba(16, 185, 129, 0.25);

      --ag-bg-base: #f5f8f5;
      --ag-surface: #ffffff;
      --ag-surface-glass: rgba(255, 255, 255, 0.85);
      
      --ag-radius-sm: 8px;
      --ag-radius-md: 14px;
      --ag-radius-lg: 20px;
      --ag-radius-pill: 9999px;

      --ag-shadow-sm: 0 2px 6px rgba(10, 35, 24, 0.04);
      --ag-shadow-md: 0 8px 24px rgba(10, 35, 24, 0.07);
      --ag-shadow-lg: 0 18px 45px rgba(10, 35, 24, 0.11);
      --ag-shadow-glow: 0 0 25px rgba(16, 185, 129, 0.22);
    }

    /* Base Typography & Background */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
      color: var(--ag-ink);
      background: radial-gradient(circle at 15% 10%, rgba(220, 252, 231, 0.45) 0%, transparent 40%),
                  radial-gradient(circle at 85% 85%, rgba(254, 243, 199, 0.3) 0%, transparent 40%),
                  var(--ag-bg-base);
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }

    /* Custom smooth scrollbar */
    ::-webkit-scrollbar { width: 7px; height: 7px; }
    ::-webkit-scrollbar-track { background: #eef2ed; }
    ::-webkit-scrollbar-thumb { background: #c5d3c8; border-radius: var(--ag-radius-pill); }
    ::-webkit-scrollbar-thumb:hover { background: var(--ag-primary); }

    [data-testid="stMainBlockContainer"] {
      max-width: 1440px;
      padding: 1.2rem 2.2rem 3rem;
      animation: ag-page-fade-in 0.5s ease-out;
    }

    #MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }

    /* Headings */
    h1, h2, h3, h4 {
      font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important;
      color: var(--ag-ink) !important;
      letter-spacing: -0.03em;
      font-weight: 750 !important;
    }
    h1:not(.ag-hero-title) {
      font-size: clamp(2rem, 3.4vw, 2.9rem) !important;
      line-height: 1.12 !important;
      background: linear-gradient(135deg, #0d3b28 20%, #165338 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    h2 {
      font-size: 1.65rem !important;
      line-height: 1.25 !important;
      margin-top: 1.2rem !important;
      margin-bottom: 0.5rem !important;
    }
    h3 {
      font-size: 1.25rem !important;
      font-weight: 700 !important;
    }
    p, li {
      color: #3b5044;
      line-height: 1.68;
      font-size: 0.96rem;
    }
    [data-testid="stCaptionContainer"] {
      color: var(--ag-muted);
      font-size: 0.86rem;
    }

    /* Glass Cards & Containers */
    [data-testid="stVerticalBlockBorderWrapper"] {
      border: 1px solid var(--ag-line) !important;
      border-radius: var(--ag-radius-md) !important;
      background: var(--ag-surface-glass) !important;
      backdrop-filter: blur(12px) !important;
      -webkit-backdrop-filter: blur(12px) !important;
      box-shadow: var(--ag-shadow-sm) !important;
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
      box-shadow: var(--ag-shadow-md), 0 0 0 1px rgba(16, 185, 129, 0.25) !important;
      transform: translateY(-3px) !important;
    }

    /* Metrics Cards */
    [data-testid="stMetric"] {
      background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(246, 250, 247, 0.85) 100%) !important;
      border: 1px solid var(--ag-line) !important;
      border-top: 3px solid var(--ag-primary) !important;
      border-radius: var(--ag-radius-md) !important;
      padding: 1.1rem 1.25rem !important;
      box-shadow: var(--ag-shadow-sm) !important;
      backdrop-filter: blur(10px) !important;
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    [data-testid="stMetric"]:hover {
      transform: translateY(-3px) !important;
      box-shadow: var(--ag-shadow-md), 0 0 18px rgba(16, 185, 129, 0.15) !important;
      border-top-color: var(--ag-primary-hover) !important;
    }
    [data-testid="stMetricLabel"] p {
      color: var(--ag-muted) !important;
      font-size: 0.84rem !important;
      font-weight: 650 !important;
      text-transform: uppercase !important;
      letter-spacing: 0.05em !important;
    }
    [data-testid="stMetricValue"] {
      color: var(--ag-forest) !important;
      font-family: 'Plus Jakarta Sans', sans-serif !important;
      font-size: 1.75rem !important;
      font-weight: 800 !important;
      letter-spacing: -0.02em !important;
    }

    /* Buttons */
    .stButton > button, [data-testid="stDownloadButton"] button {
      border-radius: 10px !important;
      font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important;
      font-weight: 650 !important;
      font-size: 0.92rem !important;
      letter-spacing: 0.01em !important;
      min-height: 2.75rem !important;
      padding: 0.5rem 1.3rem !important;
      border: 1px solid var(--ag-line) !important;
      background: #ffffff !important;
      color: var(--ag-forest) !important;
      box-shadow: 0 2px 4px rgba(10, 35, 24, 0.03) !important;
      transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    .stButton > button:hover {
      border-color: var(--ag-primary) !important;
      color: var(--ag-primary-hover) !important;
      transform: translateY(-2px) !important;
      box-shadow: 0 6px 16px rgba(16, 185, 129, 0.18) !important;
    }
    .stButton > button:active {
      transform: translateY(0) !important;
    }
    .stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"] {
      background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
      border-color: #059669 !important;
      color: #ffffff !important;
      box-shadow: 0 4px 14px var(--ag-primary-glow) !important;
    }
    .stButton > button[kind="primary"]:hover, .stButton > button[data-testid="stBaseButton-primary"]:hover {
      background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
      border-color: #047857 !important;
      color: #ffffff !important;
      box-shadow: 0 8px 24px rgba(16, 185, 129, 0.45) !important;
      transform: translateY(-2px) scale(1.01) !important;
    }

    /* Form inputs & Selectboxes */
    [data-baseweb="input"] > div, [data-baseweb="select"] > div, [data-testid="stTextArea"] textarea {
      border-radius: 9px !important;
      border-color: #d1ddd4 !important;
      background: #ffffff !important;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03) !important;
      transition: all 0.2s ease !important;
    }
    [data-baseweb="input"] > div:focus-within, [data-baseweb="select"] > div:focus-within, [data-testid="stTextArea"] textarea:focus {
      border-color: var(--ag-primary) !important;
      box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.22) !important;
    }

    /* Tabs */
    [data-baseweb="tab-list"] {
      gap: 0.5rem !important;
      border-bottom: 2px solid var(--ag-line) !important;
      padding-bottom: 2px !important;
    }
    [data-baseweb="tab"] {
      color: var(--ag-muted) !important;
      font-family: 'Plus Jakarta Sans', sans-serif !important;
      font-weight: 650 !important;
      font-size: 0.92rem !important;
      border-radius: 8px 8px 0 0 !important;
      padding: 0.6rem 1.1rem !important;
      transition: all 0.2s ease !important;
    }
    [data-baseweb="tab"]:hover {
      color: var(--ag-forest) !important;
      background: rgba(16, 185, 129, 0.06) !important;
    }
    [data-baseweb="tab"][aria-selected="true"] {
      color: var(--ag-forest) !important;
      font-weight: 750 !important;
      border-bottom: 3px solid var(--ag-primary) !important;
    }

    /* Dataframes & Tables */
    [data-testid="stDataFrame"], [data-testid="stTable"] {
      border: 1px solid var(--ag-line) !important;
      border-radius: var(--ag-radius-md) !important;
      background: #ffffff !important;
      overflow: hidden !important;
      box-shadow: var(--ag-shadow-sm) !important;
    }

    /* Alerts and Badges */
    .ag-alert {
      display: flex; gap: 0.85rem; align-items: flex-start;
      margin: 0.65rem 0; padding: 1.1rem 1.25rem;
      border: 1px solid var(--ag-line); border-left: 4px solid var(--ag-primary);
      border-radius: var(--ag-radius-md); background: #ffffff;
      box-shadow: var(--ag-shadow-sm);
      transition: transform 0.2s ease;
    }
    .ag-alert:hover { transform: translateX(3px); }
    .ag-alert-warning { border-left-color: var(--ag-gold); background: #fffcf4; }
    .ag-alert-urgent { border-left-color: #ef4444; background: #fff8f8; }
    .ag-alert-info { border-left-color: var(--ag-sky); background: #f8fbff; }

    .ag-badge {
      display: inline-flex; align-items: center; gap: 4px;
      border-radius: var(--ag-radius-pill); padding: 0.28rem 0.75rem;
      font-size: 0.78rem; font-weight: 700; letter-spacing: 0.02em;
      border: 1px solid transparent;
    }
    .ag-badge-high { color: #b91c1c; background: #fee2e2; border-color: #fca5a5; }
    .ag-badge-medium { color: #b45309; background: #fef3c7; border-color: #fde68a; }
    .ag-badge-low { color: #047857; background: #d1fae5; border-color: #a7f3d0; }
    .ag-badge-unknown { color: #4b5563; background: #f3f4f6; border-color: #e5e7eb; }

    /* Popover */
    [data-testid="stPopoverBody"] {
      border-radius: var(--ag-radius-md) !important;
      border: 1px solid var(--ag-line) !important;
      box-shadow: var(--ag-shadow-lg) !important;
      padding: 0.75rem !important;
    }

    /* Animation Keyframes */
    @keyframes ag-page-fade-in {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    @keyframes ag-radar-ping {
      0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
      70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
      100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    @keyframes ag-float-slow {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-5px); }
    }

    /* Links */
    a { color: var(--ag-forest); text-decoration: none; font-weight: 600; }
    a:hover { color: var(--ag-primary-hover); text-decoration: underline; }
    :focus-visible { outline: 3px solid var(--ag-primary) !important; outline-offset: 2px !important; }

    /* Media Queries */
    @media (max-width: 850px) {
      [data-testid="stMainBlockContainer"] { padding: 1rem 1rem 2.5rem; }
    }
    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
      }
    }
    </style>
    """)
