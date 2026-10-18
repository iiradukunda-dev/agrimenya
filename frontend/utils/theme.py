"""Shared visual system for the agrimenya Streamlit application."""
import streamlit as st


def load_theme() -> None:
    """Apply a quiet, readable visual system with no third-party asset requests."""
    st.html("""
    <style>
    :root {
      --ag-ink: #20332b;
      --ag-muted: #64736a;
      --ag-green: #276749;
      --ag-green-dark: #194b36;
      --ag-green-soft: #eaf3ec;
      --ag-earth: #b2763e;
      --ag-line: #e3e9e3;
      --ag-paper: #f5f7f3;
      --ag-surface: #ffffff;
      --ag-radius: 14px;
    }
    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
      color: var(--ag-ink); background: var(--ag-paper);
      font-family: Inter, "Segoe UI", Arial, sans-serif;
      -webkit-font-smoothing: antialiased;
    }
    [data-testid="stMainBlockContainer"] {
      max-width: 1440px; padding: 1.3rem 2.2rem 3rem;
    }
    #MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }
    h1, h2, h3 { color: var(--ag-ink) !important; letter-spacing: -0.035em; }
    h1 { font-size: clamp(2rem, 3.2vw, 2.8rem) !important; font-weight: 720 !important; line-height: 1.12 !important; }
    h2 { font-size: 1.55rem !important; font-weight: 680 !important; }
    h3 { font-size: 1.15rem !important; font-weight: 650 !important; }
    p, li { color: #47574e; line-height: 1.65; }
    [data-testid="stCaptionContainer"] { color: var(--ag-muted); }
    [data-testid="stMetric"] {
      background: var(--ag-surface); border: 1px solid var(--ag-line);
      border-radius: var(--ag-radius); padding: 1rem 1.15rem;
      box-shadow: 0 2px 8px rgba(24, 48, 34, .035);
    }
    [data-testid="stMetricLabel"] p { color: var(--ag-muted) !important; font-size: .82rem; font-weight: 600; }
    [data-testid="stMetricValue"] { color: var(--ag-green-dark) !important; font-size: 1.65rem !important; font-weight: 700 !important; }
    .stButton > button, [data-testid="stDownloadButton"] button {
      border-radius: 9px; font-weight: 600; transition: background-color .15s ease, border-color .15s ease;
      min-height: 2.65rem;
    }
    .stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"] {
      background: var(--ag-green); border-color: var(--ag-green); color: white;
    }
    .stButton > button:hover { border-color: var(--ag-green); color: var(--ag-green-dark); }
    [data-baseweb="input"] > div, [data-baseweb="select"] > div, [data-testid="stTextArea"] textarea {
      border-radius: 8px; border-color: #d5ded6; background: white;
    }
    [data-testid="stForm"], [data-testid="stExpander"],
    [data-testid="stDataFrame"], [data-testid="stTable"] {
      border: 1px solid var(--ag-line); border-radius: var(--ag-radius); background: white;
    }
    [data-testid="stAlert"] { border-radius: 10px; }
    .ag-alert { display:flex; gap:.8rem; align-items:flex-start; margin:.55rem 0; padding:1rem 1.1rem;
      border:1px solid var(--ag-line); border-left:4px solid #6a9b77; border-radius:10px; background:white; }
    .ag-alert-warning { border-left-color:#c38a32; background:#fffaf1; }
    .ag-alert-urgent { border-left-color:#b94b42; background:#fff7f5; }
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
      [data-testid="stMainBlockContainer"] { padding: 1rem 1rem 2rem; }
    }
    @media (max-width: 600px) {
      [data-testid="stMetric"] { padding: .75rem; }
      [data-testid="stMetricValue"] { font-size: 1.25rem !important; }
    }
    @media (prefers-reduced-motion: reduce) { *, *::before, *::after { scroll-behavior: auto !important; transition-duration: .01ms !important; } }
    </style>
    """)
