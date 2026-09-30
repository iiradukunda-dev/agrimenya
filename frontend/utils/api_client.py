import requests
import streamlit as st
from requests.exceptions import RequestException
import logging
from .config import API_BASE_URL, USE_MOCK_DATA
from . import mock_data
import logging

@st.cache_data(ttl=300, show_spinner=False)
def get_kpis():
    if USE_MOCK_DATA:
        return {"total_farmers": 1450000, "yield_increase": "12%", "active_cooperatives": 3400}
    try:
        response = requests.get(f"{API_BASE_URL}/kpis", timeout=10)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        logging.error(f"Error fetching KPIs: {e}")
        raise

@st.cache_data(ttl=300, show_spinner=False)
def get_priority_data():
    if USE_MOCK_DATA:
        return mock_data.generate_mock_priority_data()
    try:
        response = requests.get(f"{API_BASE_URL}/priority-zones", timeout=10)
        response.raise_for_status()
        import pandas as pd
        return pd.DataFrame(response.json())
    except RequestException as e:
        logging.error(f"Error fetching priority data: {e}")
        raise

@st.cache_data(ttl=300, show_spinner=False)
def get_recommendations():
    if USE_MOCK_DATA:
        return mock_data.generate_mock_recommendations()
    try:
        response = requests.get(f"{API_BASE_URL}/recommendations", timeout=10)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        logging.error(f"Error fetching recommendations: {e}")
        raise

@st.cache_data(ttl=300, show_spinner=False)
def get_roadmap():
    if USE_MOCK_DATA:
        return mock_data.generate_mock_roadmap()
    try:
        response = requests.get(f"{API_BASE_URL}/roadmap", timeout=10)
        response.raise_for_status()
        import pandas as pd
        return pd.DataFrame(response.json())
    except RequestException as e:
        logging.error(f"Error fetching roadmap: {e}")
        raise

@st.cache_data(ttl=300, show_spinner=False)
def get_alerts():
    if USE_MOCK_DATA:
        return mock_data.generate_mock_alerts()
    try:
        response = requests.get(f"{API_BASE_URL}/alerts", timeout=10)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        logging.error(f"Error fetching alerts: {e}")
        raise
