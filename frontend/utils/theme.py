import streamlit as st

def load_theme():
    # Inject PWA service worker and manifest
    st.html("""
    <script>
        // Register Service Worker
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/app/static/sw.js')
            .then(function(registration) {
                console.log('PWA Service Worker registered with scope:', registration.scope);
            })
            .catch(function(error) {
                console.error('PWA Service Worker registration failed:', error);
            });
        }
        
        // Inject Manifest
        if (!document.querySelector('link[rel="manifest"]')) {
            const link = document.createElement('link');
            link.rel = 'manifest';
            link.href = '/app/static/manifest.json';
            document.head.appendChild(link);
        }

        // Inject Theme Color Meta Tag
        if (!document.querySelector('meta[name="theme-color"]')) {
            const meta = document.createElement('meta');
            meta.name = 'theme-color';
            meta.content = '#52B788';
            document.head.appendChild(meta);
        }
    </script>
    """, unsafe_allow_javascript=True)

    st.html("""
        <style>
        @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes pulseGlow { 0% { box-shadow: 0 0 0 0 rgba(82, 183, 136, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(82, 183, 136, 0); } 100% { box-shadow: 0 0 0 0 rgba(82, 183, 136, 0); } }
        @keyframes floating { 0% { transform: translateY(0px); } 50% { transform: translateY(-5px); } 100% { transform: translateY(0px); } }
        @keyframes gradientMove { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }

        /* Base font and animated background */
        html, body, [class*="css"], .stApp {
            font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            color: #1B2A1E;
            background: linear-gradient(-45deg, #F9FBF9, #F0F7F2, #E8F5E9, #F9FBF9);
            background-size: 400% 400%;
            animation: gradientMove 15s ease infinite;
        }

        /* Hide Streamlit default UI elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Adjust main container padding with entry animation */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
            max-width: 1200px;
            animation: fadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }

        /* Metric Cards */
        [data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(221, 231, 223, 0.5);
            border-top: 4px solid #52B788;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 10px 20px -5px rgba(0, 0, 0, 0.05), 0 8px 16px -8px rgba(0, 0, 0, 0.01);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            animation: floating 6s ease-in-out infinite;
        }
        [data-testid="stMetric"]:hover {
            transform: translateY(-8px) scale(1.02);
            border-color: #74C69D;
            border-top-color: #2D6A4F;
            box-shadow: 0 25px 30px -10px rgba(82, 183, 136, 0.25), 0 15px 20px -15px rgba(82, 183, 136, 0.15);
        }
        
        /* Metric Label */
        [data-testid="stMetricLabel"] > div:nth-child(1) {
            font-weight: 600;
            color: #4A5D4E;
            font-size: 1rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* Metric Value */
        [data-testid="stMetricValue"] > div {
            font-weight: 800;
            background: linear-gradient(90deg, #2D6A4F, #52B788);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.5rem;
            transition: all 0.3s ease;
        }

        /* Buttons */
        .stButton>button {
            background: linear-gradient(135deg, #52B788 0%, #40916C 100%);
            color: #ffffff;
            border: none;
            border-radius: 50px;
            padding: 12px 28px;
            font-weight: 700;
            letter-spacing: 0.5px;
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
            box-shadow: 0 4px 15px rgba(82, 183, 136, 0.4);
            position: relative;
            overflow: hidden;
        }
        .stButton>button::after {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 300%;
            height: 300%;
            background: rgba(255, 255, 255, 0.2);
            transform: translate(-50%, -50%) scale(0);
            border-radius: 50%;
            transition: transform 0.5s;
        }
        .stButton>button:hover::after {
            transform: translate(-50%, -50%) scale(1);
            opacity: 0;
            transition: transform 0.5s, opacity 0.5s;
        }
        .stButton>button:hover {
            transform: translateY(-3px) scale(1.05);
            box-shadow: 0 8px 25px rgba(64, 145, 108, 0.6);
            animation: pulseGlow 1.5s infinite;
        }
        .stButton>button:active {
            transform: translateY(1px);
            box-shadow: 0 2px 10px rgba(64, 145, 108, 0.4);
        }

        /* Primary Form Submit Button */
        button[kind="primary"] {
            background: linear-gradient(135deg, #40916C 0%, #2D6A4F 100%) !important;
            border: none !important;
        }
        
        /* Custom cards for Home page */
        .custom-card {
            background: rgba(255, 255, 255, 0.85);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(221, 231, 223, 0.6);
            border-radius: 20px;
            padding: 28px;
            height: 100%;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            position: relative;
            overflow: hidden;
        }
        .custom-card::before {
            content: '';
            position: absolute;
            top: 0; left: -100%;
            width: 50%; height: 100%;
            background: linear-gradient(to right, rgba(255,255,255,0) 0%, rgba(255,255,255,0.6) 50%, rgba(255,255,255,0) 100%);
            transform: skewX(-25deg);
            transition: all 0.75s;
        }
        .custom-card:hover::before {
            left: 200%;
        }
        .custom-card:hover {
            box-shadow: 0 20px 40px rgba(82, 183, 136, 0.2);
            border-color: #52B788;
            transform: translateY(-8px) scale(1.02);
        }
        .custom-card-title {
            font-size: 1.3rem;
            font-weight: 800;
            color: #1B2A1E;
            margin-bottom: 12px;
            margin-top: 18px;
            background: linear-gradient(90deg, #1B2A1E, #2D6A4F);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .custom-card-desc {
            font-size: 0.95rem;
            color: #4A5D4E;
            line-height: 1.6;
        }

        /* Divider styling */
        hr {
            margin-top: 3rem;
            margin-bottom: 3rem;
            border: 0;
            height: 1px;
            background: linear-gradient(to right, transparent, #52B788, transparent);
            opacity: 0.5;
        }

        /* Sidebar accent */
        [data-testid="stSidebar"] {
            background: rgba(255, 255, 255, 0.95) !important;
            backdrop-filter: blur(10px);
            border-right: 1px solid rgba(226, 234, 227, 0.8);
            box-shadow: 4px 0 15px rgba(0,0,0,0.03);
        }
        [data-testid="stSidebarNav"] {
            padding-top: 2rem;
        }
        [data-testid="stSidebar"] hr {
            margin: 1.5rem 0;
            background: linear-gradient(to right, transparent, #DDE7DF, transparent);
        }
        [data-testid="stSidebarNav"] span {
            font-weight: 600;
            font-size: 1.05rem;
            color: #1B2A1E;
            transition: color 0.3s ease;
        }
        [data-testid="stSidebarNav"] a {
            transition: all 0.3s ease;
            border-radius: 12px;
            margin: 0 8px;
        }
        [data-testid="stSidebarNav"] a:hover {
            background-color: rgba(82, 183, 136, 0.15);
            transform: translateX(5px);
        }
        [data-testid="stSidebarNav"] a:hover span {
            color: #2D6A4F;
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
            border-radius: 16px;
            overflow: hidden;
            border: 1px solid rgba(226, 234, 227, 0.8);
            box-shadow: 0 4px 20px rgba(0,0,0,0.04);
            transition: box-shadow 0.3s ease;
        }
        [data-testid="stDataFrame"]:hover {
            box-shadow: 0 8px 30px rgba(82, 183, 136, 0.15);
        }
        
        /* Tabs Polish */
        [data-baseweb="tab-list"] {
            gap: 10px;
        }
        [data-baseweb="tab"] {
            border-radius: 12px 12px 0 0;
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
            font-weight: 600;
            padding: 10px 20px;
        }
        [data-baseweb="tab"]:hover {
            background-color: rgba(82, 183, 136, 0.1);
            color: #2D6A4F;
        }
        [aria-selected="true"] {
            background: linear-gradient(180deg, rgba(82, 183, 136, 0.15) 0%, transparent 100%) !important;
            border-bottom: 3px solid #52B788 !important;
            color: #2D6A4F !important;
        }
        
        /* Form Inputs Polish */
        .stTextInput>div>div>input, .stSelectbox>div>div>div, .stTextArea>div>div>textarea {
            border-radius: 12px !important;
            border: 2px solid #E2EAE3 !important;
            background-color: rgba(255, 255, 255, 0.8) !important;
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.02) !important;
        }
        .stTextInput>div>div>input:focus, .stSelectbox>div>div>div:focus-within, .stTextArea>div>div>textarea:focus {
            border-color: #52B788 !important;
            box-shadow: 0 0 0 2px rgba(82, 183, 136, 0.2) !important;
        }
        </style>
    """)

