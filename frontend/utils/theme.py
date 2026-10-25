"""Shared visual system for the agrimenya Streamlit application."""
import streamlit as st


def load_theme() -> None:
    """Apply a modern, high-contrast, polished visual system with smooth animations."""
    st.html("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

    :root {
      /* Bio-Luminescent Bulb & Foliage Theme Palette */
      --ag-cyan: #0284c7;
      --ag-cyan-light: #38bdf8;
      --ag-cyan-soft: rgba(14, 165, 233, 0.12);
      --ag-cyan-glow: rgba(56, 189, 248, 0.45);

      --ag-emerald: #10b981;
      --ag-emerald-light: #4ade80;
      --ag-emerald-soft: rgba(16, 185, 129, 0.12);
      --ag-emerald-glow: rgba(74, 222, 128, 0.42);

      --ag-primary: #0284c7;
      --ag-primary-hover: #0369a1;
      --ag-primary-soft: rgba(14, 165, 233, 0.12);
      --ag-primary-glow: rgba(14, 165, 233, 0.38);

      --ag-forest: #042f2e;
      --ag-forest-dark: #021a24;
      --ag-forest-light: #0d4b4a;

      --ag-gold: #f59e0b;
      --ag-gold-soft: rgba(245, 158, 11, 0.12);
      --ag-gold-glow: rgba(245, 158, 11, 0.35);

      --ag-sky: #0ea5e9;
      --ag-sky-soft: rgba(14, 165, 233, 0.12);

      --ag-ink: #0a1f26;
      --ag-muted: #48656c;
      --ag-line: #d8e5e8;
      --ag-line-glow: rgba(56, 189, 248, 0.28);

      --ag-bg-base: #f4f8fa;
      --ag-surface: #ffffff;
      --ag-surface-dark: #081a26;
      
      --ag-radius-sm: 8px;
      --ag-radius-md: 14px;
      --ag-radius-lg: 20px;
      --ag-radius-pill: 9999px;

      --ag-shadow-sm: 0 2px 6px rgba(4, 31, 38, 0.04);
      --ag-shadow-md: 0 8px 24px rgba(4, 31, 38, 0.08);
      --ag-shadow-lg: 0 20px 48px rgba(4, 31, 38, 0.12);
      --ag-shadow-glow: 0 0 28px rgba(56, 189, 248, 0.25);
      --ag-shadow-bulb: 0 8px 30px rgba(14, 165, 233, 0.22), 0 0 20px rgba(74, 222, 128, 0.18);
    }

    /* Base Typography & Background */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
      color: var(--ag-ink);
      background: radial-gradient(circle at 10% 8%, rgba(56, 189, 248, 0.18) 0%, transparent 45%),
                  radial-gradient(circle at 90% 88%, rgba(74, 222, 128, 0.16) 0%, transparent 45%),
                  radial-gradient(circle at 50% 50%, rgba(255, 255, 255, 0.6) 0%, transparent 70%),
                  var(--ag-bg-base);
      font-family: 'Outfit', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }

    /* Custom smooth scrollbar with bulb cyan-emerald gradient */
    ::-webkit-scrollbar { width: 7px; height: 7px; }
    ::-webkit-scrollbar-track { background: #eaf1f4; }
    ::-webkit-scrollbar-thumb { background: linear-gradient(180deg, #38bdf8 0%, #34d399 100%); border-radius: var(--ag-radius-pill); }
    ::-webkit-scrollbar-thumb:hover { background: linear-gradient(180deg, #0ea5e9 0%, #10b981 100%); }

    [data-testid="stMainBlockContainer"] {
      max-width: 1440px;
      padding: 1.2rem 2.2rem 3rem;
      animation: ag-page-fade-in 0.5s ease-out;
    }

    #MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }
    [data-testid="stSidebar"],
    [data-testid="collapsedControl"],
    section[data-testid="stSidebar"],
    aside[data-testid="stSidebar"],
    [data-testid="stSidebarNav"],
    [data-testid="stSidebarNavItems"] {
      display: none !important;
      width: 0 !important;
      max-width: 0 !important;
      min-width: 0 !important;
      visibility: hidden !important;
      pointer-events: none !important;
    }
    [data-testid="stDeployButton"],
    button[data-testid="stDeployButton"] {
      display: none !important;
    }

    /* Static Persistent Floating AI Bulb (Zero continuous animation) */
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
      text-decoration: none !important;
    }
    .ag-floating-ai-fab img {
      width: 58px !important;
      height: auto !important;
      max-height: 92px !important;
      object-fit: contain !important;
      animation: none !important;
      filter: drop-shadow(0 0 6px rgba(56, 189, 248, 0.85))
              drop-shadow(0 0 14px rgba(74, 222, 128, 0.75))
              drop-shadow(0 0 24px rgba(34, 197, 94, 0.4))
              drop-shadow(0 4px 10px rgba(0, 0, 0, 0.25)) !important;
    }

    /* Headings */
    h1, h2, h3, h4 {
      font-family: 'Plus Jakarta Sans', 'Outfit', sans-serif !important;
      color: var(--ag-ink);
      letter-spacing: -0.03em;
      font-weight: 750 !important;
    }
    h1:not(.ag-hero-title) {
      font-size: clamp(2rem, 3.4vw, 2.9rem) !important;
      line-height: 1.12 !important;
      background: linear-gradient(135deg, #022b38 0%, #064e4b 50%, #0d5c3f 100%);
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

    /* Structured Modern Cards with Classic Motion Designs */
    [data-testid="stVerticalBlockBorderWrapper"] {
      position: relative !important;
      overflow: hidden !important;
      border: 1px solid rgba(56, 189, 248, 0.22) !important;
      border-top: 1.5px solid rgba(56, 189, 248, 0.40) !important;
      border-radius: var(--ag-radius-md) !important;
      background: #081a26 !important;
      box-shadow: 0 10px 28px rgba(0, 0, 0, 0.35) !important;
      transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1),
                  box-shadow 0.35s cubic-bezier(0.16, 1, 0.3, 1),
                  border-color 0.3s ease,
                  background 0.3s ease !important;
      will-change: transform, box-shadow;
    }
    /* Subtle reflective sheen sweep across card on hover */
    [data-testid="stVerticalBlockBorderWrapper"]::after {
      content: '';
      position: absolute;
      top: -60%;
      left: -130%;
      width: 70%;
      height: 220%;
      background: linear-gradient(
        105deg,
        transparent 20%,
        rgba(255, 255, 255, 0.04) 45%,
        rgba(56, 189, 248, 0.08) 50%,
        rgba(255, 255, 255, 0.04) 55%,
        transparent 80%
      );
      transform: rotate(25deg);
      transition: left 0.85s cubic-bezier(0.16, 1, 0.3, 1);
      pointer-events: none;
      z-index: 1;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover::after {
      left: 140%;
    }
    /* Classic Elevation & Glow on Hover */
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
      box-shadow: 0 20px 48px -10px rgba(0, 0, 0, 0.65), 0 0 26px rgba(56, 189, 248, 0.30), inset 0 1px 0 rgba(255, 255, 255, 0.12) !important;
      border-color: rgba(56, 189, 248, 0.65) !important;
      border-top-color: #38bdf8 !important;
      background: #0c2435 !important;
      transform: translateY(-6px) scale(1.012) !important;
    }
    /* Tactile Active Press State */
    [data-testid="stVerticalBlockBorderWrapper"]:active {
      transform: translateY(-2px) scale(0.995) !important;
      box-shadow: 0 8px 20px rgba(0, 0, 0, 0.45), 0 0 14px rgba(56, 189, 248, 0.2) !important;
      transition: transform 0.12s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.12s ease !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] h1,
    [data-testid="stVerticalBlockBorderWrapper"] h2,
    [data-testid="stVerticalBlockBorderWrapper"] h3,
    [data-testid="stVerticalBlockBorderWrapper"] h4 {
      color: #ffffff !important;
      text-shadow: 0 2px 8px rgba(0, 0, 0, 0.7) !important;
      transition: color 0.25s ease, text-shadow 0.25s ease !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover h3 {
      text-shadow: 0 2px 12px rgba(56, 189, 248, 0.45) !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] p {
      color: #e0f2fe !important;
      text-shadow: 0 1px 6px rgba(0, 0, 0, 0.7) !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] .stButton > button,
    [data-testid="stVerticalBlockBorderWrapper"] button {
      background: #0f2738 !important;
      border: 1px solid rgba(56, 189, 248, 0.28) !important;
      border-radius: 10px !important;
      color: #ffffff !important;
      font-weight: 700 !important;
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25) !important;
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] .stButton > button *,
    [data-testid="stVerticalBlockBorderWrapper"] button * {
      color: #ffffff !important;
      font-weight: 700 !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover .stButton > button,
    [data-testid="stVerticalBlockBorderWrapper"]:hover button {
      background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
      border-color: rgba(56, 189, 248, 0.85) !important;
      box-shadow: 0 6px 20px rgba(56, 189, 248, 0.4) !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] .stButton > button:hover,
    [data-testid="stVerticalBlockBorderWrapper"] button:hover {
      background: linear-gradient(135deg, #0369a1 0%, #0284c7 100%) !important;
      border-color: #38bdf8 !important;
      color: #ffffff !important;
      box-shadow: 0 8px 24px rgba(56, 189, 248, 0.55) !important;
      transform: translateY(-2px) scale(1.02) !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] .stButton > button:active,
    [data-testid="stVerticalBlockBorderWrapper"] button:active {
      transform: translateY(0) scale(0.98) !important;
    }

    /* Metrics Cards with Classic Elevation & Glow */
    [data-testid="stMetric"] {
      background: #ffffff !important;
      border: 1px solid var(--ag-line) !important;
      border-top: 3.5px solid #0ea5e9 !important;
      border-radius: var(--ag-radius-md) !important;
      padding: 1.1rem 1.25rem !important;
      box-shadow: var(--ag-shadow-sm) !important;
      transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1),
                  box-shadow 0.35s cubic-bezier(0.16, 1, 0.3, 1),
                  border-color 0.3s ease !important;
      will-change: transform, box-shadow;
    }
    [data-testid="stMetric"]:hover {
      transform: translateY(-5px) scale(1.01) !important;
      box-shadow: 0 14px 34px rgba(4, 31, 38, 0.10), 0 0 24px rgba(56, 189, 248, 0.28) !important;
      border-top-color: #38bdf8 !important;
    }
    [data-testid="stMetric"]:active {
      transform: translateY(-1px) scale(0.995) !important;
      box-shadow: var(--ag-shadow-sm) !important;
    }
    [data-testid="stMetricLabel"] p {
      color: var(--ag-muted) !important;
      font-size: 0.84rem !important;
      font-weight: 650 !important;
      text-transform: uppercase !important;
      letter-spacing: 0.05em !important;
    }
    [data-testid="stMetricValue"] {
      color: #034b5c !important;
      font-family: 'Plus Jakarta Sans', sans-serif !important;
      font-size: 1.75rem !important;
      font-weight: 800 !important;
      letter-spacing: -0.02em !important;
    }

    /* =========================================================
       AGRIMENYA GLOBAL BUTTON ARCHITECTURE: HIGH-CONTRAST & ULTRA-CLEAR
       ========================================================= */

    /* 1. Base Button Styles (Applies to all Streamlit buttons) */
    .stButton > button,
    [data-testid="stBaseButton-secondary"],
    [data-testid="stBaseButton-primary"],
    [data-testid="stFormSubmitButton"] > button,
    [data-testid="stDownloadButton"] button {
      border-radius: 12px !important;
      font-family: 'Plus Jakarta Sans', 'Outfit', sans-serif !important;
      font-weight: 700 !important;
      font-size: 0.94rem !important;
      letter-spacing: -0.01em !important;
      min-height: 2.85rem !important;
      padding: 0.55rem 1.45rem !important;
      cursor: pointer !important;
      display: inline-flex !important;
      align-items: center !important;
      justify-content: center !important;
      gap: 0.5rem !important;
      transition: all 0.28s cubic-bezier(0.16, 1, 0.3, 1) !important;
      will-change: transform, box-shadow;
    }

    /* 2. Secondary / Standard Buttons: Crisp, high-contrast outline on light canvas */
    .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]),
    [data-testid="stBaseButton-secondary"] {
      background: #ffffff !important;
      background-color: #ffffff !important;
      border: 1.5px solid #0284c7 !important;
      color: #0284c7 !important;
      box-shadow: 0 2px 8px rgba(2, 132, 199, 0.12), 0 1px 3px rgba(0, 0, 0, 0.04) !important;
    }
    .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]) *,
    [data-testid="stBaseButton-secondary"] * {
      color: #0284c7 !important;
      font-weight: 700 !important;
    }
    .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]) span[data-testid="stIconMaterial"],
    [data-testid="stBaseButton-secondary"] span[data-testid="stIconMaterial"],
    .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]) svg,
    [data-testid="stBaseButton-secondary"] svg {
      color: #0284c7 !important;
      stroke: #0284c7 !important;
    }
    .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):hover,
    [data-testid="stBaseButton-secondary"]:hover {
      background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
      background-color: #0284c7 !important;
      border-color: #38bdf8 !important;
      color: #ffffff !important;
      box-shadow: 0 8px 24px rgba(2, 132, 199, 0.38) !important;
      transform: translateY(-2px) scale(1.01) !important;
    }
    .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):hover *,
    [data-testid="stBaseButton-secondary"]:hover * {
      color: #ffffff !important;
    }
    .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):hover span[data-testid="stIconMaterial"],
    [data-testid="stBaseButton-secondary"]:hover span[data-testid="stIconMaterial"],
    .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):hover svg,
    [data-testid="stBaseButton-secondary"]:hover svg {
      color: #ffffff !important;
      stroke: #ffffff !important;
    }
    .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):active,
    [data-testid="stBaseButton-secondary"]:active {
      transform: translateY(0) scale(0.99) !important;
    }

    /* 3. Primary Action & Form Submit Buttons: Vibrant bioluminescent cyan-to-emerald gradient */
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="stBaseButton-primary"],
    [data-testid="stBaseButton-primary"],
    [data-testid="stFormSubmitButton"] > button {
      background: linear-gradient(135deg, #0284c7 0%, #0ea5e9 35%, #10b981 85%, #059669 100%) !important;
      background-color: #0284c7 !important;
      border: 1.5px solid rgba(56, 189, 248, 0.85) !important;
      color: #ffffff !important;
      box-shadow: 0 4px 18px rgba(14, 165, 233, 0.42), 0 0 14px rgba(74, 222, 128, 0.28) !important;
      text-shadow: 0 1px 3px rgba(0, 0, 0, 0.45) !important;
    }
    .stButton > button[kind="primary"] *,
    .stButton > button[data-testid="stBaseButton-primary"] *,
    [data-testid="stBaseButton-primary"] *,
    [data-testid="stFormSubmitButton"] > button * {
      color: #ffffff !important;
      font-weight: 750 !important;
      text-shadow: 0 1px 3px rgba(0, 0, 0, 0.45) !important;
    }
    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="stBaseButton-primary"]:hover,
    [data-testid="stBaseButton-primary"]:hover,
    [data-testid="stFormSubmitButton"] > button:hover {
      background: linear-gradient(135deg, #0369a1 0%, #0284c7 35%, #059669 85%, #047857 100%) !important;
      border-color: #38bdf8 !important;
      color: #ffffff !important;
      box-shadow: 0 8px 28px rgba(14, 165, 233, 0.60), 0 0 24px rgba(74, 222, 128, 0.48) !important;
      transform: translateY(-2px) scale(1.015) !important;
    }
    .stButton > button[kind="primary"]:active,
    .stButton > button[data-testid="stBaseButton-primary"]:active,
    [data-testid="stBaseButton-primary"]:active,
    [data-testid="stFormSubmitButton"] > button:active {
      transform: translateY(0) scale(0.99) !important;
    }

    /* 4. Download / Export Buttons */
    [data-testid="stDownloadButton"] button,
    .stDownloadButton > button {
      background: #ffffff !important;
      border: 1.5px solid #10b981 !important;
      color: #047857 !important;
      box-shadow: 0 2px 8px rgba(16, 185, 129, 0.15) !important;
    }
    [data-testid="stDownloadButton"] button *,
    .stDownloadButton > button * {
      color: #047857 !important;
      font-weight: 700 !important;
    }
    [data-testid="stDownloadButton"] button:hover,
    .stDownloadButton > button:hover {
      background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
      border-color: #34d399 !important;
      color: #ffffff !important;
      box-shadow: 0 6px 20px rgba(16, 185, 129, 0.35) !important;
      transform: translateY(-2px) !important;
    }
    [data-testid="stDownloadButton"] button:hover *,
    .stDownloadButton > button:hover * {
      color: #ffffff !important;
    }

    /* 5. Buttons inside Dark Cards & Bordered Containers */
    [data-testid="stVerticalBlockBorderWrapper"] .stButton > button:not([kind="primary"]),
    [data-testid="stVerticalBlockBorderWrapper"] button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]) {
      background: linear-gradient(135deg, #0e3044 0%, #082130 100%) !important;
      border: 1.5px solid rgba(56, 189, 248, 0.55) !important;
      border-radius: 12px !important;
      color: #ffffff !important;
      font-weight: 700 !important;
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35) !important;
      transition: all 0.28s ease !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] .stButton > button:not([kind="primary"]) *,
    [data-testid="stVerticalBlockBorderWrapper"] button:not([kind="primary"]) * {
      color: #ffffff !important;
      font-weight: 700 !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] .stButton > button:not([kind="primary"]):hover,
    [data-testid="stVerticalBlockBorderWrapper"] button:not([kind="primary"]):hover {
      background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
      border-color: #38bdf8 !important;
      color: #ffffff !important;
      box-shadow: 0 8px 24px rgba(56, 189, 248, 0.5) !important;
      transform: translateY(-2px) scale(1.015) !important;
    }

    /* 6. Scoped Navbar Pill Buttons & Popovers */
    .st-key-ag_navbar [data-testid="stHorizontalBlock"] button,
    .st-key-ag_navbar [data-testid="stHorizontalBlock"] .stPopover > button,
    .st-key-ag_navbar [data-testid="stHorizontalBlock"] [data-testid="stPopover"] button {
      background: #081a26 !important;
      border-radius: 10px !important;
      min-height: 2.55rem !important;
      padding: 0.35rem 0.85rem !important;
      border: 1px solid rgba(56, 189, 248, 0.25) !important;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25) !important;
      font-family: 'Plus Jakarta Sans', sans-serif !important;
      font-size: 0.88rem !important;
      font-weight: 700 !important;
      color: #ffffff !important;
      text-shadow: 0 1px 4px rgba(0, 0, 0, 0.7) !important;
      transition: all 0.25s ease !important;
    }
    .st-key-ag_navbar [data-testid="stHorizontalBlock"] button p,
    .st-key-ag_navbar [data-testid="stHorizontalBlock"] .stPopover > button p,
    .st-key-ag_navbar [data-testid="stHorizontalBlock"] [data-testid="stPopover"] button p {
      color: #ffffff !important;
      font-family: 'Plus Jakarta Sans', sans-serif !important;
      font-weight: 700 !important;
    }
    .st-key-ag_navbar [data-testid="stHorizontalBlock"] button span[data-testid="stIconMaterial"],
    .st-key-ag_navbar [data-testid="stHorizontalBlock"] .stPopover > button span[data-testid="stIconMaterial"],
    .st-key-ag_navbar [data-testid="stHorizontalBlock"] [data-testid="stPopover"] button span[data-testid="stIconMaterial"] {
      color: #ffffff !important;
      font-family: "Material Symbols Rounded", "Material Symbols Outlined" !important;
    }
    .st-key-ag_navbar [data-testid="stHorizontalBlock"] button:hover,
    .st-key-ag_navbar [data-testid="stHorizontalBlock"] .stPopover > button:hover,
    .st-key-ag_navbar [data-testid="stHorizontalBlock"] [data-testid="stPopover"] button:hover {
      background: #0c2434 !important;
      border-color: rgba(56, 189, 248, 0.65) !important;
      box-shadow: 0 6px 20px rgba(14, 165, 233, 0.35) !important;
      transform: translateY(-1px) !important;
    }
    .st-key-ag_navbar [data-testid="stHorizontalBlock"] button:hover p,
    .st-key-ag_navbar [data-testid="stHorizontalBlock"] .stPopover > button:hover p,
    .st-key-ag_navbar [data-testid="stHorizontalBlock"] [data-testid="stPopover"] button:hover p,
    .st-key-ag_navbar [data-testid="stHorizontalBlock"] button:hover span[data-testid="stIconMaterial"],
    .st-key-ag_navbar [data-testid="stHorizontalBlock"] .stPopover > button:hover span[data-testid="stIconMaterial"] {
      color: #38bdf8 !important;
    }

    /* Transparent Landing Page Headings & Subtitles */
    .ag-section-title, h2.ag-section-title {
      color: #ffffff !important;
      -webkit-text-fill-color: #ffffff !important;
      font-family: 'Plus Jakarta Sans', sans-serif !important;
      font-size: 1.65rem !important;
      font-weight: 800 !important;
      letter-spacing: -0.03em !important;
      text-shadow: 0 2px 10px rgba(0, 0, 0, 0.8) !important;
      margin: 0 !important;
    }
    .ag-section-subtitle, p.ag-section-subtitle {
      color: #e0f2fe !important;
      -webkit-text-fill-color: #e0f2fe !important;
      font-size: 0.94rem !important;
      text-shadow: 0 1px 6px rgba(0, 0, 0, 0.8) !important;
      margin: 0.25rem 0 0 !important;
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
      border-color: #0ea5e9 !important;
      box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.25) !important;
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
      color: #0284c7 !important;
      background: rgba(14, 165, 233, 0.06) !important;
    }
    [data-baseweb="tab"][aria-selected="true"] {
      color: #042f2e !important;
      font-weight: 750 !important;
      border-bottom: 3px solid #0ea5e9 !important;
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
      border: 1px solid var(--ag-line); border-left: 4px solid #0ea5e9;
      border-radius: var(--ag-radius-md); background: #ffffff;
      box-shadow: var(--ag-shadow-sm);
      transition: transform 0.2s ease;
    }
    .ag-alert:hover { transform: translateX(3px); }
    .ag-alert-warning { border-left-color: var(--ag-gold); background: #fffcf4; }
    .ag-alert-urgent { border-left-color: #ef4444; background: #fff8f8; }
    .ag-alert-info { border-left-color: #0ea5e9; background: #f0f9ff; }

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
      border: 1px solid rgba(56, 189, 248, 0.25) !important;
      box-shadow: var(--ag-shadow-lg) !important;
      padding: 0.75rem !important;
    }

    /* Animation Keyframes */
    @keyframes ag-page-fade-in {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    @keyframes ag-radar-ping {
      0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.7); }
      70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(56, 189, 248, 0); }
      100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(56, 189, 248, 0); }
    }
    @keyframes ag-float-slow {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-5px); }
    }

    /* Links */
    a { color: #0284c7; text-decoration: none; font-weight: 600; }
    a:hover { color: #0369a1; text-decoration: underline; }
    :focus-visible { outline: 3px solid #38bdf8 !important; outline-offset: 2px !important; }

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
