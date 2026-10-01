import requests
import streamlit as st
from requests.exceptions import RequestException
import logging
import pandas as pd
from .config import API_BASE_URL, USE_MOCK_DATA
from . import mock_data

def _get_api(path: str, timeout=10):
    url = f"{API_BASE_URL}{path}"
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logging.error(f"API Error fetching {url}: {e}")
        return None

@st.cache_data(ttl=300, show_spinner=False)
def get_kpis():
    if USE_MOCK_DATA:
        return {"total_farmers": 1450000, "yield_increase": "12%", "active_cooperatives": 3400}
    
    # Try fetching health to check if backend is online
    data = _get_api("/health")
    if data:
        # Construct KPIs from health if possible, otherwise use fallback data but show online status
        return {
            "total_farmers": 1450000, 
            "yield_increase": f"{data.get('baselines_overall_average', 0):.1f} MT/ha Avg" if data.get('baselines_overall_average') else "12%", 
            "active_cooperatives": 3400
        }
    return {"total_farmers": 1450000, "yield_increase": "12%", "active_cooperatives": 3400}

@st.cache_data(ttl=300, show_spinner=False)
def get_priority_data():
    if USE_MOCK_DATA:
        return mock_data.generate_mock_priority_data()
        
    data = _get_api("/segmentation/map-data")
    if data:
        df = pd.DataFrame(data)
        if not df.empty:
            df.rename(columns={
                'latitude': 'Lat',
                'longitude': 'Lon',
                'priority_level': 'Priority',
                'predicted_yield': 'Yield_MT_ha',
                'district': 'District'
            }, inplace=True)
            if 'Crop' not in df.columns:
                df['Crop'] = 'Maize' # Fallback default if not in backend
            return df
            
    return mock_data.generate_mock_priority_data()

@st.cache_data(ttl=300, show_spinner=False)
def get_recommendations():
    if USE_MOCK_DATA:
        return mock_data.generate_mock_recommendations()
        
    rankings = _get_api("/decision/priority-ranking")
    if rankings and isinstance(rankings, list):
        recs = []
        for r in rankings[:5]: # Top 5
            zone_id = r.get("zone_id")
            crop = r.get("crop", "Unknown")
            priority = r.get("priority_level", "Medium")
            district = r.get("zones", {}).get("district", "Unknown") if r.get("zones") else "Unknown"
            
            rec_data = _get_api(f"/decision/recommendations/{zone_id}")
            if rec_data:
                texts = rec_data.get("recommendations", [])
                text = " ".join(texts) if texts else "No detailed recommendations."
            else:
                text = "No detailed recommendations available."
                
            recs.append({
                "area": district,
                "crop": crop,
                "priority": priority,
                "text": text,
                "status": "Pending"
            })
        if recs:
            return recs
    return mock_data.generate_mock_recommendations()

@st.cache_data(ttl=300, show_spinner=False)
def get_roadmap():
    if USE_MOCK_DATA:
        return mock_data.generate_mock_roadmap()
    
    zones = _get_api("/segmentation/zones")
    if zones and len(zones) > 0:
        zone_id = zones[0].get("id")
        plans = _get_api(f"/planification/plans/{zone_id}")
        if plans and isinstance(plans, list) and len(plans) > 0:
            latest_plan = plans[0]
            roadmap_json = latest_plan.get("roadmap_json", [])
            if roadmap_json:
                mapped = []
                for step in roadmap_json:
                    mapped.append({
                        "Task": step.get("task", "Unknown"),
                        "Start": step.get("start_date", "2026-01-01"),
                        "End": step.get("end_date", "2026-01-31"),
                        "Phase": step.get("phase", "Execution")
                    })
                if mapped:
                    return pd.DataFrame(mapped)
                
    return mock_data.generate_mock_roadmap()

@st.cache_data(ttl=300, show_spinner=False)
def get_alerts():
    if USE_MOCK_DATA:
        return mock_data.generate_mock_alerts()
        
    alerts = _get_api("/communication/alerts")
    if alerts and isinstance(alerts, list):
        mapped = []
        for a in alerts:
            mapped.append({
                "type": "Warning" if a.get("is_urgent") else "Info",
                "message": a.get("message", ""),
                "timestamp": str(a.get("created_at", ""))[:10]
            })
        if mapped:
            return mapped
        
    return mock_data.generate_mock_alerts()

def send_alert(message: str, target_group: str, is_urgent: bool):
    if USE_MOCK_DATA:
        return True
    
    url = f"{API_BASE_URL}/communication/alerts"
    payload = {
        "message": message,
        "target_group": target_group,
        "is_urgent": is_urgent,
        "created_by": "System"
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        get_alerts.clear()
        return True
    except Exception as e:
        logging.error(f"Error sending alert to {url}: {e}")
        return False
