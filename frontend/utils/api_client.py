import requests
from .config import API_BASE_URL, USE_MOCK_DATA
from . import mock_data

def get_kpis():
    if USE_MOCK_DATA:
        return {"total_farmers": 1450000, "yield_increase": "12%", "active_cooperatives": 3400}
    # response = requests.get(f"{API_BASE_URL}/kpis")
    # return response.json()

def get_priority_data():
    if USE_MOCK_DATA:
        return mock_data.generate_mock_priority_data()
    # response = requests.get(f"{API_BASE_URL}/priority-zones")
    # return pd.DataFrame(response.json())

def get_recommendations():
    if USE_MOCK_DATA:
        return mock_data.generate_mock_recommendations()

def get_roadmap():
    if USE_MOCK_DATA:
        return mock_data.generate_mock_roadmap()

def get_alerts():
    if USE_MOCK_DATA:
        return mock_data.generate_mock_alerts()
