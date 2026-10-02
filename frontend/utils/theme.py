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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap');

    :root {
        --lg-bg-hue1: #52B788;
        --lg-bg-hue2: #74C69D;
        --lg-bg-hue3: #2D6A4F;
        --lg-bg-hue4: #40916C;
        
        --lg-glass-fill: linear-gradient(135deg, rgba(255, 255, 255, 0.4), rgba(255, 255, 255, 0.1));
        --lg-glass-border: rgba(255, 255, 255, 0.4);
        --lg-glass-blur: blur(24px) saturate(180%) brightness(1.05);
        --lg-glass-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
        --lg-glass-highlight: inset 0 1px 0 rgba(255, 255, 255, 0.6), inset 0 -1px 0 rgba(255, 255, 255, 0.1);
        
        --lg-radius-card: 24px;
        --lg-radius-pill: 50px;
        
        --lg-text-primary: #1B2A1E;
        --lg-text-secondary: #4A5D4E;
        
        --lg-easing: cubic-bezier(0.22, 1, 0.36, 1);
    }

    /* Ambient Background Orbs */
    .lg-bg-container {
        position: fixed;
        inset: 0;
        z-index: -1;
        overflow: hidden;
        background-color: #F0F7F2;
    }
    .lg-orb {
        position: absolute;
        border-radius: 50%;
        filter: blur(80px);
        opacity: 0.6;
        animation: orbDrift 25s infinite alternate ease-in-out;
    }
    .lg-orb-1 { width: 600px; height: 600px; background: var(--lg-bg-hue1); top: -10%; left: -10%; }
    .lg-orb-2 { width: 500px; height: 500px; background: var(--lg-bg-hue2); bottom: -10%; right: -5%; animation-delay: -5s; }
    .lg-orb-3 { width: 700px; height: 700px; background: var(--lg-bg-hue3); top: 40%; left: 40%; animation-delay: -10s; }

    @keyframes orbDrift {
        0% { transform: translate(0, 0) scale(1); }
        50% { transform: translate(100px, 50px) scale(1.1); }
        100% { transform: translate(-50px, 100px) scale(0.9); }
    }
    
    @keyframes slideUpFade {
        from { opacity: 0; transform: translateY(30px); filter: blur(5px); }
        to { opacity: 1; transform: translateY(0); filter: blur(0); }
    }

    /* Global Fonts & Reset */
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', sans-serif;
        color: var(--lg-text-primary);
        background: transparent !important;
    }
    h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; }

    /* Hide Streamlit Clutter */
    #MainMenu, footer, header { visibility: hidden; }

    /* Glass Surface Mixin (for metric cards) */
    [data-testid="stMetric"] {
        background: var(--lg-glass-fill);
        backdrop-filter: var(--lg-glass-blur);
        -webkit-backdrop-filter: var(--lg-glass-blur);
        border: 1px solid var(--lg-glass-border);
        box-shadow: var(--lg-glass-shadow), var(--lg-glass-highlight);
        border-radius: var(--lg-radius-card);
        padding: 24px;
        transition: all 0.4s var(--lg-easing);
        animation: slideUpFade 0.8s var(--lg-easing) forwards;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 25px 30px -10px rgba(82, 183, 136, 0.25), 0 15px 20px -15px rgba(82, 183, 136, 0.15);
    }
    
    /* Main Container */
    .block-container {
        padding-top: 3rem !important;
        animation: slideUpFade 0.8s var(--lg-easing) forwards;
    }

    /* Sidebar Glass */
    [data-testid="stSidebar"] {
        background: rgba(255,255,255,0.2) !important;
        backdrop-filter: blur(30px) saturate(200%);
        -webkit-backdrop-filter: blur(30px) saturate(200%);
        border-right: 1px solid var(--lg-glass-border);
        box-shadow: inset -1px 0 0 rgba(255,255,255,0.2);
    }
    
    /* Buttons */
    .stButton > button {
        background: var(--lg-glass-fill);
        backdrop-filter: var(--lg-glass-blur);
        border: 1px solid var(--lg-glass-border);
        border-radius: var(--lg-radius-pill);
        box-shadow: var(--lg-glass-shadow), var(--lg-glass-highlight);
        color: var(--lg-text-primary);
        font-weight: 600;
        transition: transform 0.3s var(--lg-easing), box-shadow 0.3s var(--lg-easing);
        position: relative;
        overflow: hidden;
    }
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0; left: -100%;
        width: 50%; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.8), transparent);
        transform: skewX(-20deg);
        transition: left 0.5s var(--lg-easing);
    }
    .stButton > button:hover::before { left: 200%; }
    .stButton > button:hover {
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 12px 24px rgba(0,0,0,0.15), var(--lg-glass-highlight);
        color: var(--lg-text-primary);
        border-color: rgba(255,255,255,0.8);
    }
    .stButton > button:active {
        transform: scale(0.96);
    }

    /* Primary Button */
    button[kind="primary"] {
        background: linear-gradient(135deg, #52B788, #2D6A4F) !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.3) !important;
    }

    /* Inputs */
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stTextArea>div>div>textarea {
        background: rgba(255,255,255,0.3) !important;
        backdrop-filter: blur(10px);
        border: 1px solid var(--lg-glass-border) !important;
        border-radius: var(--lg-radius-pill) !important;
        color: var(--lg-text-primary) !important;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.05) !important;
        transition: all 0.3s var(--lg-easing) !important;
    }
    .stTextInput>div>div>input:focus, .stSelectbox>div>div>div:focus-within {
        background: rgba(255,255,255,0.6) !important;
        box-shadow: 0 0 0 3px rgba(82, 183, 136, 0.3), inset 0 2px 4px rgba(0,0,0,0.05) !important;
        border-color: #52B788 !important;
    }
    
    /* Chat Messages */
    [data-testid="stChatMessage"] {
        background: var(--lg-glass-fill);
        backdrop-filter: var(--lg-glass-blur);
        border: 1px solid var(--lg-glass-border);
        border-radius: var(--lg-radius-card);
        padding: 1rem;
        box-shadow: var(--lg-glass-shadow), var(--lg-glass-highlight);
        margin-bottom: 1rem;
    }
    
    /* Tabs */
    [data-baseweb="tab-list"] {
        background: rgba(255,255,255,0.2);
        backdrop-filter: blur(10px);
        border-radius: var(--lg-radius-pill);
        padding: 4px;
        border: 1px solid var(--lg-glass-border);
    }
    [data-baseweb="tab"] {
        border-radius: var(--lg-radius-pill);
        transition: all 0.3s var(--lg-easing);
    }
    [aria-selected="true"] {
        background: white !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        color: var(--lg-text-primary) !important;
    }

    /* Custom cards for Home page */
    .custom-card {
        background: var(--lg-glass-fill);
        backdrop-filter: var(--lg-glass-blur);
        -webkit-backdrop-filter: var(--lg-glass-blur);
        border: 1px solid var(--lg-glass-border);
        border-radius: var(--lg-radius-card);
        padding: 28px;
        height: 100%;
        box-shadow: var(--lg-glass-shadow), var(--lg-glass-highlight);
        transition: all 0.4s var(--lg-easing);
        position: relative;
        overflow: hidden;
    }
    .custom-card::before {
        content: '';
        position: absolute;
        top: 0; left: -100%;
        width: 50%; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.6), transparent);
        transform: skewX(-25deg);
        transition: left 0.75s var(--lg-easing);
    }
    .custom-card:hover::before {
        left: 200%;
    }
    .custom-card:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 20px 40px rgba(82, 183, 136, 0.2);
        border-color: #52B788;
    }
    .custom-card-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.3rem;
        font-weight: 800;
        color: var(--lg-text-primary);
        margin-bottom: 12px;
        margin-top: 18px;
        background: linear-gradient(90deg, #1B2A1E, #2D6A4F);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .custom-card-desc {
        font-size: 0.95rem;
        color: var(--lg-text-secondary);
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

    </style>
    
    <div class="lg-bg-container">
        <div class="lg-orb lg-orb-1"></div>
        <div class="lg-orb lg-orb-2"></div>
        <div class="lg-orb lg-orb-3"></div>
    </div>
    """, unsafe_allow_javascript=True)
