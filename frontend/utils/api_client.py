import requests
from .config import API_BASE_URL, USE_MOCK_DATA
from . import mock_data

import requests
from requests.exceptions import RequestException
import logging

def get_kpis():
    if USE_MOCK_DATA:
        return {"total_farmers": 1450000, "yield_increase": "12%", "active_cooperatives": 3400}
    try:
        response = requests.get(f"{API_BASE_URL}/kpis", timeout=10)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        logging.error(f"Error fetching KPIs: {e}")
        return {"total_farmers": "N/A", "yield_increase": "N/A", "active_cooperatives": "N/A"}

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
        import pandas as pd
        return pd.DataFrame()

def get_recommendations():
    if USE_MOCK_DATA:
        return mock_data.generate_mock_recommendations()
    try:
        response = requests.get(f"{API_BASE_URL}/recommendations", timeout=10)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        logging.error(f"Error fetching recommendations: {e}")
        return []

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
        import pandas as pd
        return pd.DataFrame()

def get_alerts():
    if USE_MOCK_DATA:
        return mock_data.generate_mock_alerts()
    try:
        response = requests.get(f"{API_BASE_URL}/alerts", timeout=10)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        logging.error(f"Error fetching alerts: {e}")
        return []
