import streamlit as st
from utils.i18n import t, render_language_selector

def render_navbar():
    """
    Renders a custom top navigation bar, completely hiding the default Streamlit sidebar.
    """
    st.markdown("""
        <style>
        /* Hide sidebar and default hamburger menu/header */
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }
        header[data-testid="stHeader"] { display: none !important; }
        
        .block-container {
            padding-top: 1.5rem !important;
        }
        
        /* Style for page links to look like a modern navbar */
        div[data-testid="stPageLink-NavLink"] {
            background-color: #ffffff;
            border: 1px solid #E2EAE3;
            border-radius: 8px;
            padding: 8px 12px;
            transition: all 0.2s ease;
            text-align: center;
        }
        div[data-testid="stPageLink-NavLink"]:hover {
            background-color: #E8F5E9;
            border-color: #74C69D;
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(82, 183, 136, 0.1);
        }
        /* Active state */
        div[data-testid="stPageLink-NavLink"][aria-current="page"],
        div[data-testid="stPageLink-NavLink"][data-active="true"] {
            background-color: #52B788 !important;
            border-color: #52B788 !important;
        }
        div[data-testid="stPageLink-NavLink"][aria-current="page"] p,
        div[data-testid="stPageLink-NavLink"][data-active="true"] p {
            color: #ffffff !important;
            font-weight: 600;
        }
        
        /* Animations for components (Fade in up) */
        @keyframes fade-in-up {
            from {
                opacity: 0;
                transform: translateY(12px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        [data-testid="stMetric"], .custom-card, [data-testid="stMarkdownContainer"] > div > svg {
            animation: fade-in-up 0.5s ease-out forwards;
        }
        .element-container {
            animation: fade-in-up 0.4s ease-out forwards;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Render the navbar links horizontally
    cols = st.columns([1.5, 1.5, 1.5, 1.5, 1.5, 0.5, 2])
    with cols[0]:
        st.page_link("Home.py", label=t("home.app_title"), icon="🌾")
    with cols[1]:
        st.page_link("pages/1_Decision_Making.py", label=t("pillar.decisions.title"), icon="🧠")
    with cols[2]:
        st.page_link("pages/2_Planification.py", label=t("pillar.planification.title"), icon="📅")
    with cols[3]:
        st.page_link("pages/3_Segmentation.py", label=t("pillar.segmentation.title"), icon="🗺️")
    with cols[4]:
        st.page_link("pages/4_Communication.py", label=t("pillar.communication.title"), icon="💬")
    
    with cols[6]:
        # Language selector inline in the navbar
        render_language_selector(sidebar=False)
        
    st.divider()
