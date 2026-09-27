import streamlit as st
import streamlit.components.v1 as components

def load_theme():
    # Inject PWA service worker and manifest into the parent window
    components.html("""
    <script>
        const parentWindow = window.parent;
        
        // Register Service Worker
        if ('serviceWorker' in parentWindow.navigator) {
            parentWindow.navigator.serviceWorker.register('/app/static/sw.js')
            .then(function(registration) {
                console.log('PWA Service Worker registered with scope:', registration.scope);
            })
            .catch(function(error) {
                console.error('PWA Service Worker registration failed:', error);
            });
        }
        
        // Inject Manifest
        if (!parentWindow.document.querySelector('link[rel="manifest"]')) {
            const link = parentWindow.document.createElement('link');
            link.rel = 'manifest';
            link.href = '/app/static/manifest.json';
            parentWindow.document.head.appendChild(link);
        }

        // Inject Theme Color Meta Tag
        if (!parentWindow.document.querySelector('meta[name="theme-color"]')) {
            const meta = parentWindow.document.createElement('meta');
            meta.name = 'theme-color';
            meta.content = '#2D6A4F';
            parentWindow.document.head.appendChild(meta);
        }
    </script>
    """, height=0, width=0)

    st.markdown("""
        <style>
        /* Import Google Font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        /* Base font and background */
        html, body, [class*="css"]  {
            font-family: 'Inter', sans-serif;
            color: #1B2A1E;
        }

        /* Hide Streamlit default UI elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Adjust main container padding */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
            max-width: 1200px;
        }

        /* Metric Cards */
        [data-testid="stMetric"] {
            background-color: #ffffff;
            border: 1px solid #DDE7DF;
            border-top: 3px solid #2D6A4F;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.04), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
            transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out, border-color 0.2s ease-in-out;
        }
        [data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            border-color: #52B788;
            border-top-color: #1B4332;
            box-shadow: 0 10px 15px -3px rgba(45, 106, 79, 0.08), 0 4px 6px -2px rgba(45, 106, 79, 0.04);
        }
        
        /* Metric Label */
        [data-testid="stMetricLabel"] > div:nth-child(1) {
            font-weight: 600;
            color: #4A5D4E;
            font-size: 0.95rem;
        }
        
        /* Metric Value */
        [data-testid="stMetricValue"] > div {
            font-weight: 700;
            color: #2D6A4F;
            font-size: 2rem;
        }

        /* Buttons */
        .stButton>button {
            background-color: #2D6A4F;
            color: #ffffff;
            border: none;
            border-radius: 8px;
            padding: 10px 24px;
            font-weight: 600;
            transition: all 0.2s ease;
            box-shadow: 0 2px 4px rgba(45, 106, 79, 0.2);
        }
        .stButton>button:hover {
            background-color: #1B4332;
            color: #ffffff;
            box-shadow: 0 4px 8px rgba(27, 67, 50, 0.3);
            transform: translateY(-1px);
        }
        .stButton>button:active {
            background-color: #132A13;
            transform: translateY(0);
        }

        /* Primary Form Submit Button */
        button[kind="primary"] {
            background-color: #2D6A4F !important;
            border-color: #2D6A4F !important;
        }
        button[kind="primary"]:hover {
            background-color: #1B4332 !important;
            border-color: #1B4332 !important;
        }
        
        /* Custom cards for Home page */
        .custom-card {
            background-color: #ffffff;
            border: 1px solid #DDE7DF;
            border-radius: 12px;
            padding: 24px;
            height: 100%;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.02);
            transition: all 0.3s ease;
        }
        .custom-card:hover {
            box-shadow: 0 10px 18px rgba(45, 106, 79, 0.08);
            border-color: #52B788;
            transform: translateY(-2px);
        }
        .custom-card-title {
            font-size: 1.15rem;
            font-weight: 700;
            color: #1B2A1E;
            margin-bottom: 10px;
            margin-top: 14px;
        }
        .custom-card-desc {
            font-size: 0.88rem;
            color: #4A5D4E;
            line-height: 1.5;
        }

        /* Divider styling */
        hr {
            margin-top: 2rem;
            margin-bottom: 2rem;
            border-top: 1px solid #E2EAE3;
        }

        /* Sidebar accent */
        [data-testid="stSidebar"] {
            background-color: #F3F8F3;
            border-right: 1px solid #E2EAE3;
        }
        [data-testid="stSidebarNav"] {
            padding-top: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)
