"""Shared visual system and design tokens for the agrimenya application."""
import streamlit as st


def get_current_theme() -> str:
    """Return the active theme mode ('light' or 'dark')."""
    return st.session_state.get("ag_theme_mode", "light")


def toggle_theme() -> None:
    """Toggle between light and dark theme modes."""
    current = get_current_theme()
    st.session_state["ag_theme_mode"] = "dark" if current == "light" else "light"


def load_theme(show_sidebar: bool = False) -> None:
    """Apply a modern, high-contrast, professional visual system with dark/light mode support."""
    theme_mode = get_current_theme()
    is_dark = theme_mode == "dark"

    # Dynamic CSS variable values based on active theme mode
    bg_base = "#09111c" if is_dark else "#f8fafc"
    bg_subtle = "#0f1c2e" if is_dark else "#f0f9ff"
    surface = "#111c2e" if is_dark else "#ffffff"
    surface_hover = "#16243b" if is_dark else "#f0f9ff"
    card_bg = "#111c2e" if is_dark else "#ffffff"
    card_border = "rgba(56, 189, 248, 0.22)" if is_dark else "rgba(2, 132, 199, 0.16)"
    card_shadow = "0 10px 25px -5px rgba(0,0,0,0.45)" if is_dark else "0 2px 12px -2px rgba(2, 132, 199, 0.08), 0 1px 3px rgba(0, 0, 0, 0.04)"
    card_shadow_hover = "0 16px 32px -4px rgba(0,0,0,0.6), 0 0 20px rgba(56,189,248,0.25)" if is_dark else "0 8px 24px -4px rgba(2, 132, 199, 0.18), 0 2px 6px -1px rgba(0, 0, 0, 0.04)"
    
    text_main = "#f8fafc" if is_dark else "#0f172a"
    text_muted = "#94a3b8" if is_dark else "#334155"
    text_subtle = "#64748b" if is_dark else "#64748b"
    border_color = "rgba(56, 189, 248, 0.18)" if is_dark else "rgba(2, 132, 199, 0.16)"
    input_bg = "#0a1524" if is_dark else "#ffffff"
    input_border = "rgba(56, 189, 248, 0.3)" if is_dark else "rgba(2, 132, 199, 0.25)"
    metric_bg = "#111c2e" if is_dark else "#ffffff"
    sidebar_suppression = "" if show_sidebar else """
    [data-testid="stSidebar"], [data-testid="collapsedControl"],
    section[data-testid="stSidebar"], aside[data-testid="stSidebar"] {
      display: none !important;
      width: 0 !important;
      visibility: hidden !important;
    }
    """
    sidebar_navigation_css = """
    [data-testid="stSidebar"], section[data-testid="stSidebar"], aside[data-testid="stSidebar"] {
      display: flex !important; visibility: visible !important; pointer-events: auto !important;
    }
    [data-testid="collapsedControl"] { display: flex !important; visibility: visible !important; }
    [data-testid="stSidebarNav"] { display: none !important; }
    [data-testid="stSidebarContent"] { padding-top: 1rem !important; }
    """ if show_sidebar else ""

    st.html(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

    :root {{
      /* Design Tokens: Agriculture Emerald, Brand Sky/Cyan, Accents */
      --ag-primary: #0284c7;
      --ag-primary-hover: #0369a1;
      --ag-primary-soft: rgba(2, 132, 199, 0.12);
      
      --ag-emerald: #10b981;
      --ag-emerald-hover: #059669;
      --ag-emerald-soft: rgba(16, 185, 129, 0.12);

      --ag-forest: #1b4332;
      --ag-forest-dark: #0f2e22;

      --ag-success: #10b981;
      --ag-warning: #f59e0b;
      --ag-danger: #ef4444;
      --ag-info: #0ea5e9;

      /* Active Theme Dynamic Tokens */
      --ag-bg-base: {bg_base};
      --ag-bg-subtle: {bg_subtle};
      --ag-surface: {surface};
      --ag-surface-hover: {surface_hover};
      --ag-card-bg: {card_bg};
      --ag-card-border: {card_border};
      --ag-card-shadow: {card_shadow};
      --ag-card-shadow-hover: {card_shadow_hover};
      --ag-text-main: {text_main};
      --ag-text-muted: {text_muted};
      --ag-text-subtle: {text_subtle};
      --ag-border: {border_color};
      --ag-input-bg: {input_bg};
      --ag-input-border: {input_border};
      --ag-metric-bg: {metric_bg};

      /* Radii */
      --ag-radius-sm: 6px;
      --ag-radius-md: 12px;
      --ag-radius-lg: 18px;
      --ag-radius-pill: 9999px;

      /* Typography Scale */
      --ag-font-sans: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      --ag-font-display: 'Plus Jakarta Sans', var(--ag-font-sans);
    }}

    /* Global Viewport Background */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {{
      color: var(--ag-text-main);
      background-color: var(--ag-bg-base);
      font-family: var(--ag-font-sans);
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
      transition: background-color 0.25s ease, color 0.25s ease;
    }}

    /* Hide Streamlit default chrome headers */
    header[data-testid="stHeader"],
    .stApp > header,
    [data-testid="stHeader"],
    #MainMenu,
    footer,
    #ag-pwa-install-badge,
    [id="ag-pwa-install-badge"],
    [id*="pwa-install"],
    .viewerBadge_container,
    [class*="viewerBadge"],
    [data-testid="manage-app-button"],
    [data-testid="stDecoration"],
    [data-testid="stToolbar"] {{
      display: none !important;
      height: 0 !important;
      visibility: hidden !important;
    }}

    /* Main Container Spacing */
    .block-container,
    [data-testid="stMainBlockContainer"],
    [data-testid="stAppViewBlockContainer"],
    .main .block-container {{
      max-width: 1440px;
      padding-top: 0.35rem !important;
      padding-left: 2rem !important;
      padding-right: 2rem !important;
      padding-bottom: 3.5rem !important;
      margin-top: 0 !important;
      animation: ag-fade-in 0.3s ease-out;
    }}

    {sidebar_suppression}
    {sidebar_navigation_css}

    /* Typography */
    h1, h2, h3, h4, h5, h6 {{
      font-family: var(--ag-font-display) !important;
      color: var(--ag-text-main) !important;
      letter-spacing: -0.025em;
      font-weight: 750 !important;
      margin-bottom: 0.4rem;
    }}
    h1 {{
      font-size: clamp(1.8rem, 2.8vw, 2.4rem) !important;
      line-height: 1.2 !important;
    }}
    h2 {{
      font-size: 1.45rem !important;
      line-height: 1.3 !important;
    }}
    h3 {{
      font-size: 1.15rem !important;
      font-weight: 700 !important;
    }}
    p, li, span {{
      color: var(--ag-text-muted);
      font-size: 0.94rem;
      line-height: 1.6;
    }}

    /* Clean Card System (st.container(border=True)) */
    [data-testid="stVerticalBlockBorderWrapper"] {{
      background: var(--ag-card-bg) !important;
      border: 1px solid var(--ag-card-border) !important;
      border-radius: var(--ag-radius-md) !important;
      box-shadow: var(--ag-card-shadow) !important;
      padding: 0.5rem 0.2rem !important;
      margin-bottom: 0.75rem !important;
      transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1),
                  box-shadow 0.2s cubic-bezier(0.16, 1, 0.3, 1),
                  border-color 0.2s ease !important;
    }}
    [data-testid="stVerticalBlockBorderWrapper"]:hover {{
      border-color: rgba(2, 132, 199, 0.4) !important;
      box-shadow: var(--ag-card-shadow-hover) !important;
    }}
    [data-testid="stVerticalBlockBorderWrapper"] p {{
      color: var(--ag-text-muted) !important;
    }}
    [data-testid="stVerticalBlockBorderWrapper"] h1,
    [data-testid="stVerticalBlockBorderWrapper"] h2,
    [data-testid="stVerticalBlockBorderWrapper"] h3,
    [data-testid="stVerticalBlockBorderWrapper"] h4 {{
      color: var(--ag-text-main) !important;
    }}

    /* Modern KPI Metric Cards */
    [data-testid="stMetric"] {{
      background: var(--ag-metric-bg) !important;
      border: 1px solid var(--ag-card-border) !important;
      border-top: 3px solid var(--ag-primary) !important;
      border-radius: var(--ag-radius-md) !important;
      padding: 1rem 1.15rem !important;
      box-shadow: var(--ag-card-shadow) !important;
      transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    [data-testid="stMetric"]:hover {{
      transform: translateY(-2px);
      box-shadow: var(--ag-card-shadow-hover) !important;
      border-top-color: var(--ag-emerald) !important;
    }}
    [data-testid="stMetricLabel"] p {{
      color: var(--ag-text-muted) !important;
      font-size: 0.82rem !important;
      font-weight: 600 !important;
      letter-spacing: 0.02em !important;
      text-transform: uppercase !important;
    }}
    [data-testid="stMetricValue"] div {{
      font-family: var(--ag-font-display) !important;
      color: var(--ag-text-main) !important;
      font-weight: 800 !important;
      font-size: 1.85rem !important;
      letter-spacing: -0.03em !important;
    }}

    /* Form Inputs and Select Boxes */
    [data-baseweb="input"] > div,
    [data-baseweb="select"] > div,
    [data-testid="stTextArea"] textarea {{
      background: var(--ag-input-bg) !important;
      border: 1px solid var(--ag-input-border) !important;
      border-radius: var(--ag-radius-sm) !important;
      color: var(--ag-text-main) !important;
      transition: all 0.2s ease !important;
    }}
    [data-baseweb="input"] input,
    [data-baseweb="select"] input,
    [data-testid="stTextArea"] textarea {{
      color: var(--ag-text-main) !important;
      font-family: var(--ag-font-sans) !important;
      font-size: 0.92rem !important;
    }}
    [data-baseweb="input"] > div:focus-within,
    [data-baseweb="select"] > div:focus-within,
    [data-testid="stTextArea"] textarea:focus {{
      border-color: var(--ag-primary) !important;
      box-shadow: 0 0 0 3px rgba(2, 132, 199, 0.25) !important;
    }}

    /* Primary and Secondary Buttons (excluding tabs) */
    .stButton > button:not([role="tab"]):not([data-baseweb="tab"]) {{
      border-radius: var(--ag-radius-sm) !important;
      font-family: var(--ag-font-display) !important;
      font-weight: 650 !important;
      font-size: 0.90rem !important;
      padding: 0.45rem 1.1rem !important;
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
      border: 1px solid var(--ag-card-border) !important;
      background: var(--ag-surface) !important;
      color: var(--ag-text-main) !important;
      box-shadow: var(--ag-card-shadow) !important;
    }}
    .stButton > button:not([role="tab"]):not([data-baseweb="tab"]):hover {{
      border-color: var(--ag-primary) !important;
      color: var(--ag-primary) !important;
      transform: translateY(-1px) !important;
      box-shadow: 0 4px 12px rgba(2, 132, 199, 0.15) !important;
    }}
    .stButton > button:not([role="tab"]):not([data-baseweb="tab"]):active {{
      transform: translateY(0) !important;
    }}
    .stButton > button[kind="primary"]:not([role="tab"]):not([data-baseweb="tab"]) {{
      background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
      color: #ffffff !important;
      border: none !important;
      box-shadow: 0 2px 8px rgba(2, 132, 199, 0.3) !important;
    }}
    .stButton > button[kind="primary"]:not([role="tab"]):not([data-baseweb="tab"]):hover {{
      background: linear-gradient(135deg, #0369a1 0%, #0284c7 100%) !important;
      box-shadow: 0 6px 16px rgba(2, 132, 199, 0.45) !important;
      color: #ffffff !important;
    }}

    /* Popover Trigger Buttons and Containers */
    button[data-testid="stPopoverButton"],
    [data-testid="stPopover"] > button {{
      border-radius: var(--ag-radius-sm) !important;
      font-family: var(--ag-font-display) !important;
      font-weight: 650 !important;
      font-size: 0.90rem !important;
      padding: 0.45rem 1.1rem !important;
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
      border: 1px solid var(--ag-card-border) !important;
      background: var(--ag-surface) !important;
      color: var(--ag-text-main) !important;
      box-shadow: var(--ag-card-shadow) !important;
    }}
    button[data-testid="stPopoverButton"]:hover,
    [data-testid="stPopover"] > button:hover {{
      border-color: var(--ag-primary) !important;
      color: var(--ag-primary) !important;
      box-shadow: 0 4px 12px rgba(2, 132, 199, 0.15) !important;
    }}
    [data-testid="stPopoverBody"] {{
      background: var(--ag-surface) !important;
      border: 1px solid var(--ag-card-border) !important;
      border-radius: var(--ag-radius-md) !important;
      box-shadow: var(--ag-card-shadow-hover) !important;
      color: var(--ag-text-main) !important;
      padding: 1rem !important;
    }}
    [data-testid="stPopoverBody"] p,
    [data-testid="stPopoverBody"] label,
    [data-testid="stPopoverBody"] span {{
      color: var(--ag-text-main) !important;
    }}

    /* Modal Dialog High Contrast */
    [data-testid="stDialog"] {{
      border-radius: var(--ag-radius-lg) !important;
      border: 1px solid var(--ag-card-border) !important;
      box-shadow: 0 20px 45px rgba(2, 132, 199, 0.2) !important;
      background: var(--ag-surface) !important;
    }}
    [data-testid="stDialog"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stDialog"] label {{
      color: var(--ag-text-main) !important;
      font-weight: 500;
    }}

    /* Modern Tabs */
    [data-testid="stTabs"] {{
      margin: 0.5rem 0 !important;
    }}
    [data-testid="stTabs"] [data-baseweb="tab-list"],
    [data-baseweb="tab-list"] {{
      gap: 0.4rem !important;
      border-bottom: 2px solid var(--ag-border) !important;
      padding-bottom: 2px !important;
      background: transparent !important;
    }}
    [data-testid="stTabs"] button[role="tab"],
    [data-baseweb="tab"] {{
      color: var(--ag-text-muted) !important;
      font-family: var(--ag-font-display) !important;
      font-weight: 600 !important;
      font-size: 0.90rem !important;
      border-radius: var(--ag-radius-sm) var(--ag-radius-sm) 0 0 !important;
      padding: 0.55rem 1rem !important;
      transition: all 0.2s ease !important;
      border: none !important;
      background: transparent !important;
    }}
    [data-testid="stTabs"] button[role="tab"]:hover,
    [data-baseweb="tab"]:hover {{
      color: var(--ag-primary) !important;
      background: var(--ag-primary-soft) !important;
    }}
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"],
    [data-baseweb="tab"][aria-selected="true"] {{
      color: var(--ag-primary) !important;
      font-weight: 750 !important;
      border-bottom: 3px solid var(--ag-primary) !important;
    }}
    [data-baseweb="tab-highlight"] {{
      background-color: var(--ag-primary) !important;
      height: 3px !important;
    }}

    /* Data Tables & Dataframes */
    [data-testid="stDataFrame"], [data-testid="stTable"] {{
      border: 1px solid var(--ag-border) !important;
      border-radius: var(--ag-radius-md) !important;
      background: var(--ag-card-bg) !important;
      overflow: hidden !important;
      box-shadow: var(--ag-card-shadow) !important;
    }}

    /* Semantic Alerts */
    .ag-alert {{
      display: flex;
      gap: 0.85rem;
      align-items: flex-start;
      margin: 0.6rem 0;
      padding: 0.9rem 1.15rem;
      border: 1px solid var(--ag-border);
      border-left: 4px solid var(--ag-info);
      border-radius: var(--ag-radius-md);
      background: var(--ag-surface);
      box-shadow: var(--ag-card-shadow);
      transition: transform 0.2s ease;
    }}
    .ag-alert:hover {{ transform: translateX(3px); }}
    .ag-alert-warning {{ border-left-color: var(--ag-warning); background: {'rgba(245, 158, 11, 0.08)' if is_dark else '#fffcf0'}; }}
    .ag-alert-urgent {{ border-left-color: var(--ag-danger); background: {'rgba(239, 68, 68, 0.08)' if is_dark else '#fef2f2'}; }}
    .ag-alert-info {{ border-left-color: var(--ag-info); background: {'rgba(14, 165, 233, 0.08)' if is_dark else '#f0f9ff'}; }}

    /* Priority Badges */
    .ag-badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      border-radius: var(--ag-radius-pill);
      padding: 0.25rem 0.75rem;
      font-size: 0.78rem;
      font-weight: 700;
      letter-spacing: 0.02em;
      border: 1px solid transparent;
    }}
    .ag-badge-dot {{
      width: 7px;
      height: 7px;
      border-radius: 50%;
    }}
    .ag-badge-high {{
      color: #ef4444;
      background: rgba(239, 68, 68, 0.12);
      border-color: rgba(239, 68, 68, 0.28);
    }}
    .ag-badge-high .ag-badge-dot {{ background: #ef4444; }}
    .ag-badge-medium {{
      color: #f59e0b;
      background: rgba(245, 158, 11, 0.12);
      border-color: rgba(245, 158, 11, 0.28);
    }}
    .ag-badge-medium .ag-badge-dot {{ background: #f59e0b; }}
    .ag-badge-low {{
      color: #10b981;
      background: rgba(16, 185, 129, 0.12);
      border-color: rgba(16, 185, 129, 0.28);
    }}
    .ag-badge-low .ag-badge-dot {{ background: #10b981; }}
    .ag-badge-unknown {{
      color: var(--ag-text-muted);
      background: var(--ag-bg-subtle);
      border-color: var(--ag-border);
    }}
    .ag-badge-unknown .ag-badge-dot {{ background: var(--ag-text-muted); }}

    /* Custom Executive KPI Card */
    .ag-kpi-card {{
      background: var(--ag-card-bg);
      border: 1px solid var(--ag-card-border);
      border-radius: var(--ag-radius-md);
      padding: 1.1rem 1.25rem;
      box-shadow: var(--ag-card-shadow);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      height: 100%;
      min-height: 140px;
      position: relative;
      overflow: hidden;
      transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.2s ease, border-color 0.2s ease;
    }}
    .ag-kpi-card:hover {{
      transform: translateY(-2px);
      box-shadow: var(--ag-card-shadow-hover);
      border-color: rgba(2, 132, 199, 0.45);
    }}
    .ag-kpi-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 0.5rem;
    }}
    .ag-kpi-title {{
      font-size: 0.80rem;
      font-weight: 650;
      color: var(--ag-text-muted);
      letter-spacing: 0.04em;
      text-transform: uppercase;
      margin: 0;
    }}
    .ag-kpi-icon {{
      width: 32px;
      height: 32px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--ag-primary-soft);
      color: var(--ag-primary);
    }}
    .ag-kpi-body {{
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 0.5rem;
      margin-top: auto;
    }}
    .ag-kpi-value {{
      font-family: var(--ag-font-display);
      font-size: 1.85rem;
      font-weight: 800;
      color: var(--ag-text-main);
      letter-spacing: -0.03em;
      line-height: 1.1;
      margin: 0;
    }}
    .ag-kpi-sparkline {{
      flex-shrink: 0;
    }}
    .ag-kpi-footer {{
      display: flex;
      align-items: center;
      gap: 6px;
      margin-top: 0.6rem;
      font-size: 0.78rem;
      color: var(--ag-text-muted);
    }}
    .ag-kpi-delta {{
      font-weight: 700;
      display: inline-flex;
      align-items: center;
      gap: 2px;
    }}
    .ag-kpi-delta-up {{ color: #10b981; }}
    .ag-kpi-delta-down {{ color: #ef4444; }}

    /* Weather Visual Forecast Cards */
    .ag-weather-row {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
      gap: 0.65rem;
      margin: 0.75rem 0 1rem;
    }}
    .ag-weather-card {{
      background: var(--ag-surface);
      border: 1px solid var(--ag-card-border);
      border-radius: var(--ag-radius-sm);
      padding: 0.85rem 0.75rem;
      text-align: center;
      box-shadow: var(--ag-card-shadow);
      transition: transform 0.2s ease, border-color 0.2s ease;
    }}
    .ag-weather-card:hover {{
      transform: translateY(-2px);
      border-color: var(--ag-primary);
    }}
    .ag-weather-date {{
      font-size: 0.75rem;
      font-weight: 700;
      color: var(--ag-text-muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    .ag-weather-temp {{
      font-family: var(--ag-font-display);
      font-size: 1.15rem;
      font-weight: 800;
      color: var(--ag-text-main);
      margin: 0.3rem 0;
    }}
    .ag-weather-rain {{
      font-size: 0.75rem;
      color: #0284c7;
      font-weight: 600;
    }}

    /* Empty States */
    .ag-empty-state {{
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 2.5rem 1.5rem;
      border: 1.5px dashed var(--ag-border);
      border-radius: var(--ag-radius-md);
      background: var(--ag-bg-subtle);
      text-align: center;
      margin: 1rem 0;
    }}
    .ag-empty-icon {{
      width: 48px;
      height: 48px;
      border-radius: 12px;
      background: var(--ag-primary-soft);
      color: var(--ag-primary);
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 0.85rem;
    }}
    .ag-empty-title {{
      font-family: var(--ag-font-display);
      font-size: 1.05rem;
      font-weight: 700;
      color: var(--ag-text-main);
      margin: 0 0 0.35rem;
    }}
    .ag-empty-desc {{
      font-size: 0.88rem;
      color: var(--ag-text-muted);
      max-width: 420px;
      margin: 0;
    }}

    /* Skeleton Loaders */
    .ag-skeleton {{
      background: linear-gradient(90deg, var(--ag-border) 25%, var(--ag-bg-subtle) 50%, var(--ag-border) 75%);
      background-size: 200% 100%;
      animation: ag-skeleton-pulse 1.5s infinite;
      border-radius: var(--ag-radius-sm);
    }}
    @keyframes ag-skeleton-pulse {{
      0% {{ background-position: 200% 0; }}
      100% {{ background-position: -200% 0; }}
    }}

    /* Subtle Entry Fade */
    @keyframes ag-fade-in {{
      from {{ opacity: 0; transform: translateY(6px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}

    /* Floating AI FAB */
    .ag-floating-ai-fab {{
      position: fixed !important;
      bottom: 24px !important;
      right: 24px !important;
      z-index: 9999999 !important;
      cursor: pointer !important;
    }}

    /* Focus Rings & Accessibility */
    :focus-visible {{
      outline: 2px solid var(--ag-primary) !important;
      outline-offset: 2px !important;
    }}

    /* Calm, consistent surfaces across every Streamlit page */
    [data-testid="stAppViewContainer"] {{
      background-image: radial-gradient(ellipse at 50% -18%, rgba(14, 165, 233, 0.075), transparent 42%) !important;
    }}
    .block-container,
    [data-testid="stMainBlockContainer"],
    [data-testid="stAppViewBlockContainer"],
    .main .block-container {{
      max-width: 1360px !important;
      padding-left: clamp(1rem, 3vw, 2.5rem) !important;
      padding-right: clamp(1rem, 3vw, 2.5rem) !important;
    }}
    [data-testid="stVerticalBlockBorderWrapper"] {{
      border-radius: 16px !important;
      box-shadow: 0 1px 2px rgba(15, 23, 42, 0.035), 0 8px 24px rgba(15, 23, 42, 0.045) !important;
    }}
    [data-testid="stVerticalBlockBorderWrapper"]:hover {{
      transform: translateY(-2px) !important;
      box-shadow: 0 8px 24px rgba(15, 23, 42, 0.09) !important;
    }}
    [data-testid="stMetric"] {{
      border: 1px solid var(--ag-border) !important;
      border-top: 1px solid var(--ag-border) !important;
      border-radius: 16px !important;
      box-shadow: 0 1px 2px rgba(15, 23, 42, 0.035), 0 8px 24px rgba(15, 23, 42, 0.045) !important;
    }}
    [data-baseweb="input"] > div,
    [data-baseweb="select"] > div,
    [data-testid="stTextArea"] textarea {{
      min-height: 42px;
      border-radius: 10px !important;
    }}
    .stButton > button:not([role="tab"]):not([data-baseweb="tab"]),
    button[data-testid="stPopoverButton"] {{
      min-height: 40px;
      border-radius: 10px !important;
      box-shadow: none !important;
    }}
    [data-testid="stDataFrame"],
    [data-testid="stTable"] {{
      border-radius: 14px !important;
    }}
    @media (max-width: 768px) {{
      .block-container,
      [data-testid="stMainBlockContainer"],
      [data-testid="stAppViewBlockContainer"],
      .main .block-container {{
        padding-top: 0.25rem !important;
        padding-bottom: 2rem !important;
      }}
      h1 {{ font-size: clamp(1.6rem, 7vw, 2rem) !important; }}
      [data-testid="stMetric"] {{ padding: 0.85rem !important; }}
      [data-testid="stMetricValue"] div {{ font-size: 1.5rem !important; }}
    }}

    @media (prefers-reduced-motion: reduce) {{
      *, *::before, *::after {{
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
      }}
    }}
    </style>
    """)
