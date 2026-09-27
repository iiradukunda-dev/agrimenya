import streamlit as st

def load_theme():
    st.markdown("""
        <style>
        /* Import Google Font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        /* Base font and background */
        html, body, [class*="css"]  {
            font-family: 'Inter', sans-serif;
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
            border: 1px solid #e0e0e0;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
        }
        [data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }
        
        /* Metric Label */
        [data-testid="stMetricLabel"] > div:nth-child(1) {
            font-weight: 600;
            color: #4a5568;
            font-size: 1rem;
        }
        
        /* Metric Value */
        [data-testid="stMetricValue"] > div {
            font-weight: 700;
            color: #1a202c;
            font-size: 2rem;
        }

        /* Buttons */
        .stButton>button {
            background-color: #2b6cb0;
            color: #ffffff;
            border: none;
            border-radius: 8px;
            padding: 10px 24px;
            font-weight: 600;
            transition: all 0.2s ease;
            box-shadow: 0 2px 4px rgba(43, 108, 176, 0.2);
        }
        .stButton>button:hover {
            background-color: #2c5282;
            color: #ffffff;
            box-shadow: 0 4px 8px rgba(43, 108, 176, 0.3);
            transform: translateY(-1px);
        }
        
        /* Custom cards for Home page */
        .custom-card {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 24px;
            height: 100%;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.02);
            transition: all 0.3s ease;
        }
        .custom-card:hover {
            box-shadow: 0 10px 15px rgba(0, 0, 0, 0.05);
            border-color: #cbd5e0;
            transform: translateY(-2px);
        }
        .custom-card-title {
            font-size: 1.125rem;
            font-weight: 700;
            color: #2d3748;
            margin-bottom: 12px;
            margin-top: 16px;
        }
        .custom-card-desc {
            font-size: 0.875rem;
            color: #718096;
            line-height: 1.5;
        }

        /* Divider styling */
        hr {
            margin-top: 2rem;
            margin-bottom: 2rem;
            border-top: 1px solid #e2e8f0;
        }
        </style>
    """, unsafe_allow_html=True)
