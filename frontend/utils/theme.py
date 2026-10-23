"""Shared visual system for the agrimenya Streamlit application."""
import streamlit as st


def load_theme() -> None:
    """Apply a quiet, readable visual system with no third-party asset requests."""
    st.html("""
    <style>
    :root {
      --ag-forest: #163B2A;
      --ag-ink: #18251D;
      --ag-muted: #647067;
      --ag-green: #246B45;
      --ag-green-dark: #163B2A;
      --ag-green-fresh: #4D8B52;
      --ag-green-soft: #EDF4ED;
      --ag-earth: #B2763E;
      --ag-line: #E2E8DF;
      --ag-paper: #F8FAF5;
      --ag-surface: #ffffff;
      --ag-warning: #D99A24;
      --ag-critical: #C63F3F;
      --ag-info: #3977C3;
      --ag-radius: 12px;
    }
    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
      color: var(--ag-ink); background: var(--ag-paper);
      font-family: Inter, "Segoe UI", Arial, sans-serif;
      -webkit-font-smoothing: antialiased;
    }
    [data-testid="stMainBlockContainer"] {
      max-width: 1480px; padding: 1.15rem 2.25rem 3.25rem;
    }
    #MainMenu, footer { visibility: hidden; height: 0; }
    header[data-testid="stHeader"] { visibility: visible; height: 3rem; background: transparent; }
    /* Keep Streamlit's hamburger/sidebar toggle; hide only its developer deploy action. */
    .stAppDeployButton,
    .stDeployButton,
    [data-testid="stAppDeployButton"],
    [data-testid="stToolbarActions"],
    header [data-testid="stToolbarActions"],
    header button[title*="Deploy" i],
    header button[aria-label*="Deploy" i],
    .stAppToolbar button[title*="Deploy" i] {
      display: none !important;
      visibility: hidden !important;
      width: 0 !important;
      height: 0 !important;
      overflow: hidden !important;
      opacity: 0 !important;
      pointer-events: none !important;
    }
    h1, h2, h3 { color: var(--ag-ink) !important; letter-spacing: -0.035em; }
    h1 { font-size: clamp(1.8rem, 2.75vw, 2.45rem) !important; font-weight: 720 !important; line-height: 1.13 !important; }
    h2 { font-size: 1.42rem !important; font-weight: 680 !important; }
    h3 { font-size: 1.08rem !important; font-weight: 650 !important; }
    p, li { color: #47574e; line-height: 1.65; }
    [data-testid="stCaptionContainer"] { color: var(--ag-muted); }
    [data-testid="stMetric"] {
      background: var(--ag-surface); border: 1px solid var(--ag-line);
      border-radius: var(--ag-radius); padding: 1rem 1.15rem;
      box-shadow: 0 1px 3px rgba(24, 48, 34, .035);
    }
    [data-testid="stMetricLabel"] p { color: var(--ag-muted) !important; font-size: .82rem; font-weight: 600; }
    [data-testid="stMetricValue"] { color: var(--ag-green-dark) !important; font-size: 1.65rem !important; font-weight: 700 !important; }
    .stButton > button, [data-testid="stDownloadButton"] button {
      border-radius: 9px; font-weight: 600; transition: background-color .15s ease, border-color .15s ease;
      min-height: 2.75rem;
    }
    .stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"] {
      background: var(--ag-green); border-color: var(--ag-green); color: white;
    }
    .stButton > button:hover { border-color: var(--ag-green); color: var(--ag-green-dark); }
    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="stBaseButton-primary"]:hover {
      background: var(--ag-green-dark); border-color: var(--ag-green-dark); color: white;
    }
    [data-baseweb="input"] > div, [data-baseweb="select"] > div, [data-testid="stTextArea"] textarea {
      border-radius: 8px; border-color: #d5ded6; background: white;
    }
    [data-testid="stForm"], [data-testid="stExpander"],
    [data-testid="stDataFrame"], [data-testid="stTable"] {
      border: 1px solid var(--ag-line); border-radius: var(--ag-radius); background: white;
    }
    [data-testid="stForm"] { padding: 1rem 1.1rem; }
    [data-testid="stExpander"] summary { min-height: 2.8rem; }
    [data-testid="stPageLink-NavLink"] { border-radius: 9px; min-height: 2.75rem; }
    [data-testid="stPageLink-NavLink"] p { font-weight: 600; }
    [data-testid="stRadio"] label, [data-testid="stCheckbox"] label { min-height: 2.35rem; }
    [data-testid="stAlert"] { border-radius: 10px; border:1px solid var(--ag-line); }
    .ag-alert { display:flex; gap:.8rem; align-items:flex-start; margin:.55rem 0; padding:1rem 1.1rem;
      border:1px solid var(--ag-line); border-left:4px solid #6a9b77; border-radius:10px; background:white; }
    .ag-alert-warning { border-left-color:var(--ag-warning); background:#fffaf1; }
    .ag-alert-urgent { border-left-color:var(--ag-critical); background:#fff7f5; }
    .ag-alert-info { border-left-color:#58846a; background:#f8fbf8; }
    .ag-badge { display:inline-flex; align-items:center; border-radius:999px; padding:.25rem .65rem;
      font-size:.78rem; line-height:1.25; font-weight:650; border:1px solid transparent; }
    .ag-badge-high { color:#923b34; background:#fff0ed; border-color:#f1c7c0; }
    .ag-badge-medium { color:#80591c; background:#fff8e7; border-color:#ecd8a7; }
    .ag-badge-low { color:#286246; background:#edf6ef; border-color:#c9e2cf; }
    .ag-badge-unknown { color:#56645b; background:#f1f3f0; border-color:#dce2dc; }
    .ag-error-container { max-width:560px; margin:2rem auto; padding:2rem; text-align:center;
      border:1px solid var(--ag-line); border-radius:var(--ag-radius); background:white; }
    .ag-error-details { margin:1rem 0; padding:.8rem; text-align:left; overflow-wrap:anywhere;
      border-radius:8px; background:#f4f6f3; color:#58675d; font-size:.84rem; }
    [data-testid="stPlotlyChart"] { border-radius: var(--ag-radius); }
    [data-baseweb="tab-list"] { gap: .35rem; border-bottom: 1px solid var(--ag-line); }
    [data-baseweb="tab"] { color: var(--ag-muted); font-weight: 600; }
    [data-baseweb="tab"][aria-selected="true"] { color: var(--ag-green-dark); }
    a { color: var(--ag-green); }
    :focus-visible { outline: 3px solid #87b69a !important; outline-offset: 2px !important; }
    @media (max-width: 850px) {
      [data-testid="stMainBlockContainer"] { padding: 1rem 1.1rem 2rem; }
    }
    @media (max-width: 600px) {
      h1 { font-size: 1.8rem !important; }
      h2 { font-size: 1.35rem !important; }
      [data-testid="stMainBlockContainer"] { padding: .8rem .75rem 1.5rem; }
      [data-testid="stMetric"] { padding: .75rem; }
      [data-testid="stMetricValue"] { font-size: 1.25rem !important; }
      [data-testid="stForm"] { padding: .8rem; }
      [data-testid="stDataFrame"] { overflow-x: auto; }
    }
    @media (prefers-reduced-motion: reduce) { *, *::before, *::after { scroll-behavior: auto !important; transition-duration: .01ms !important; } }
    </style>
    """)
