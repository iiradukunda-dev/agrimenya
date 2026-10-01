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
            meta.content = '#52B788';
            parentWindow.document.head.appendChild(meta);
        }
    </script>
    """, height=0, width=0)

    st.markdown("""
        <style>
        /* Base font and background */
        html, body, [class*="css"], .stApp {
            font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol';
            color: #1B2A1E;
            background-color: #F9FBF9;
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
            border-top: 3px solid #52B788;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.04), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
            transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out, border-color 0.2s ease-in-out;
        }
        [data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            border-color: #74C69D;
            border-top-color: #40916C;
            box-shadow: 0 10px 15px -3px rgba(82, 183, 136, 0.15), 0 4px 6px -2px rgba(82, 183, 136, 0.08);
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
            color: #40916C;
            font-size: 2rem;
        }

        /* Buttons */
        .stButton>button {
            background-color: #52B788;
            color: #ffffff;
            border: none;
            border-radius: 8px;
            padding: 10px 24px;
            font-weight: 600;
            transition: all 0.2s ease;
            box-shadow: 0 2px 4px rgba(82, 183, 136, 0.3);
        }
        .stButton>button:hover {
            background-color: #40916C;
            color: #ffffff;
            box-shadow: 0 4px 8px rgba(64, 145, 108, 0.4);
            transform: translateY(-1px);
        }
        .stButton>button:active {
            background-color: #2D6A4F;
            transform: translateY(0);
        }

        /* Primary Form Submit Button */
        button[kind="primary"] {
            background-color: #52B788 !important;
            border-color: #52B788 !important;
        }
        button[kind="primary"]:hover {
            background-color: #40916C !important;
            border-color: #40916C !important;
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
            box-shadow: 0 10px 18px rgba(82, 183, 136, 0.12);
            border-color: #74C69D;
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
            background-color: #ffffff !important;
            border-right: 1px solid #E2EAE3;
            box-shadow: 2px 0 5px rgba(0,0,0,0.02);
        }
        [data-testid="stSidebarNav"] {
            padding-top: 1.5rem;
        }
        [data-testid="stSidebar"] hr {
            margin: 1rem 0;
            border-top: 1px solid #E2EAE3;
        }
        [data-testid="stSidebarNav"] span {
            font-weight: 500;
            font-size: 1rem;
            color: #1B2A1E;
        }
        [data-testid="stSidebarNav"] a:hover {
            background-color: #E8F5E9;
            border-radius: 8px;
        }

        /* Responsive adjustments */
        @media (max-width: 768px) {
            .block-container {
                padding-top: 1rem !important;
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }
            [data-testid="stMetricValue"] > div {
                font-size: 1.5rem;
            }
            .custom-card {
                padding: 16px;
            }
            .custom-card-title {
                font-size: 1.05rem;
            }
        }

        /* Dataframes & Tables Polish */
        [data-testid="stDataFrame"] {
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #E2EAE3;
        }
        
        /* Tabs Polish */
        [data-baseweb="tab"] {
            border-radius: 8px 8px 0 0;
            transition: background-color 0.2s ease, color 0.2s ease;
        }
        [data-baseweb="tab"]:hover {
            background-color: #F0F7F2;
        }
        
        /* Form Inputs Polish */
        .stTextInput>div>div>input, .stSelectbox>div>div>div, .stTextArea>div>div>textarea {
            border-radius: 8px !important;
            border: 1px solid #DDE7DF !important;
            transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
        }
        .stTextInput>div>div>input:focus, .stSelectbox>div>div>div:focus-within, .stTextArea>div>div>textarea:focus {
            border-color: #52B788 !important;
            box-shadow: 0 0 0 2px rgba(82, 183, 136, 0.2) !important;
        }
        </style>
    """, unsafe_allow_html=True)

