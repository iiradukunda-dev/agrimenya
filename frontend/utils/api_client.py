"""
Extended API client methods for agrimenya frontend.

Covers all backend modules documented in the frontend handoff:
- Decision, Segmentation, Alignment, Chat/AI, Planning, Communication, Live Data, Admin.
"""
import logging
from typing import Any

import requests
import streamlit as st

from .config import API_BASE_URL, USE_MOCK_DATA
from . import mock_data

logger = logging.getLogger(__name__)


# ── Internal helpers ─────────────────────────────────────────────────

def _get_api(path: str, timeout: int = 10) -> dict[str, Any] | list[Any] | None:
    """GET request to the FastAPI backend, returns parsed JSON or None."""
    url = f"{API_BASE_URL}{path}"
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error("API GET %s failed: %s", url, e)
        return None


def _post_api(path: str, payload: dict | None = None, timeout: int = 15) -> dict[str, Any] | None:
    """POST request to the FastAPI backend, returns parsed JSON or None."""
    url = f"{API_BASE_URL}{path}"
    try:
        resp = requests.post(url, json=payload or {}, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error("API POST %s failed: %s", url, e)
        return None


def _post_api_file(path: str, files: dict, data: dict | None = None, timeout: int = 30) -> dict[str, Any] | None:
    """POST multipart/form-data to the FastAPI backend."""
    url = f"{API_BASE_URL}{path}"
    try:
        resp = requests.post(url, files=files, data=data or {}, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error("API POST (file) %s failed: %s", url, e)
        return None


# ═══════════════════════════════════════════════════════════════════
# DASHBOARD / KPIs
# ═══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def get_kpis() -> dict[str, Any]:
    """High-level KPIs for the dashboard."""
    if USE_MOCK_DATA:
        return {"total_farmers": 1_450_000, "yield_increase": "12%", "active_cooperatives": 3_400}

    data = _get_api("/health")
    if data:
        return {
            "total_farmers": 1_450_000,
            "yield_increase": (
                f"{data.get('baselines_overall_average', 0):.1f} MT/ha Avg"
                if data.get("baselines_overall_average")
                else "12%"
            ),
            "active_cooperatives": 3_400,
        }
    return {"total_farmers": 1_450_000, "yield_increase": "12%", "active_cooperatives": 3_400}


@st.cache_data(ttl=300, show_spinner=False)
def get_alignment_dashboard() -> dict[str, Any]:
    """Fetches alignment dashboard KPIs from /alignment/dashboard."""
    if USE_MOCK_DATA:
        return {
            "total_zones": 30,
            "high_priority_zones": 8,
            "avg_credit_readiness": 62.4,
            "export_ready_zones": 5,
            "estimated_jobs": 12_500,
        }
    data = _get_api("/alignment/dashboard")
    if data:
        return data
    return {
        "total_zones": 30,
        "high_priority_zones": 8,
        "avg_credit_readiness": 62.4,
        "export_ready_zones": 5,
        "estimated_jobs": 12_500,
    }


# ═══════════════════════════════════════════════════════════════════
# SEGMENTATION
# ═══════════════════════════════════════════════════════════════════

import pandas as pd


@st.cache_data(ttl=300, show_spinner=False)
def get_priority_data() -> pd.DataFrame:
    """Segmentation map data for prioritizing agricultural zones."""
    if USE_MOCK_DATA:
        return mock_data.generate_mock_priority_data()

    data = _get_api("/segmentation/map-data")
    if data:
        df = pd.DataFrame(data)
        if not df.empty:
            df.rename(columns={
                "latitude": "Lat",
                "longitude": "Lon",
                "priority_level": "Priority",
                "predicted_yield": "Yield_MT_ha",
                "district": "District",
            }, inplace=True)
            if "Crop" not in df.columns:
                df["Crop"] = "Maize"
            return df

    return mock_data.generate_mock_priority_data()


@st.cache_data(ttl=300, show_spinner=False)
def get_zones() -> list[dict[str, Any]]:
    """Returns all zones from the backend."""
    if USE_MOCK_DATA:
        return mock_data.generate_mock_zones()
    data = _get_api("/segmentation/zones")
    if data and isinstance(data, list):
        return data
    return mock_data.generate_mock_zones()


@st.cache_data(ttl=300, show_spinner=False)
def get_zone_detail(zone_id: int) -> dict[str, Any] | None:
    """Returns detail for a single zone."""
    data = _get_api(f"/segmentation/zones/{zone_id}")
    return data


@st.cache_data(ttl=300, show_spinner=False)
def get_agri_metrics() -> list[dict[str, Any]]:
    """Returns agri metrics from segmentation."""
    if USE_MOCK_DATA:
        return mock_data.generate_mock_agri_metrics()
    data = _get_api("/segmentation/agri-metrics")
    if data and isinstance(data, list):
        return data
    return mock_data.generate_mock_agri_metrics()


@st.cache_data(ttl=300, show_spinner=False)
def get_crop_comparison(district: str) -> list[dict[str, Any]]:
    """Returns crop comparison for a district."""
    data = _get_api(f"/segmentation/crop-comparison/{district}")
    if data and isinstance(data, list):
        return data
    return []


# ═══════════════════════════════════════════════════════════════════
# DECISION
# ═══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def get_recommendations() -> list[dict[str, Any]]:
    """Fetches decision-making recommendations based on priority rankings."""
    if USE_MOCK_DATA:
        return mock_data.generate_mock_recommendations()

    rankings = _get_api("/decision/priority-ranking")
    if rankings and isinstance(rankings, list):
        recs = []
        for r in rankings[:5]:
            zone_id = r.get("zone_id")
            crop = r.get("crop", "Unknown")
            priority = r.get("priority_level", "Medium")
            district = r.get("zones", {}).get("district", "Unknown") if r.get("zones") else "Unknown"

            rec_data = _get_api(f"/decision/recommendations/{zone_id}")
            texts = rec_data.get("recommendations", []) if rec_data else []
            text = " ".join(texts) if texts else "No detailed recommendations."

            recs.append({
                "area": district,
                "crop": crop,
                "priority": priority,
                "text": text,
                "status": "Pending",
            })
        if recs:
            return recs
    return mock_data.generate_mock_recommendations()


@st.cache_data(ttl=300, show_spinner=False)
def get_priority_ranking() -> list[dict[str, Any]]:
    """Fetches the full priority ranking list."""
    data = _get_api("/decision/priority-ranking")
    if data and isinstance(data, list):
        return data
    return []


@st.cache_data(ttl=300, show_spinner=False)
def get_crops() -> list[str]:
    """Returns available crops from the decision module."""
    data = _get_api("/decision/crops")
    if data and isinstance(data, list):
        return data
    return mock_data.CROPS


def predict_yield(payload: dict[str, Any]) -> dict[str, Any] | None:
    """POST /decision/predict to get yield prediction."""
    return _post_api("/decision/predict", payload)


def get_zone_recommendations(zone_id: int) -> dict[str, Any] | None:
    """GET /decision/recommendations/{zone_id}."""
    return _get_api(f"/decision/recommendations/{zone_id}")


# ═══════════════════════════════════════════════════════════════════
# ALIGNMENT
# ═══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def get_finance_readiness(zone_id: int) -> dict[str, Any] | None:
    """Finance readiness for a zone."""
    return _get_api(f"/alignment/finance-readiness/{zone_id}")


@st.cache_data(ttl=300, show_spinner=False)
def get_nutrition_risk(zone_id: int) -> dict[str, Any] | None:
    """Nutrition risk assessment for a zone."""
    return _get_api(f"/alignment/nutrition-risk/{zone_id}")


@st.cache_data(ttl=300, show_spinner=False)
def get_export_flags() -> list[dict[str, Any]]:
    """Export readiness flags across zones."""
    data = _get_api("/alignment/export-flags")
    if data and isinstance(data, list):
        return data
    return []


# ═══════════════════════════════════════════════════════════════════
# CHAT / AI ASSISTANT
# ═══════════════════════════════════════════════════════════════════

def chat(message: str, zone_id: int | None = None) -> dict[str, Any] | None:
    """Sends a message to the AI assistant."""
    payload: dict[str, Any] = {"message": message}
    if zone_id is not None:
        payload["zone_id"] = zone_id
    return _post_api("/chat", payload)


def disease_detect(crop: str, symptoms: str) -> dict[str, Any] | None:
    """Text-based disease detection."""
    return _post_api("/chat/disease-detect", {"crop": crop, "symptoms": symptoms})


def disease_detect_upload(crop: str, symptoms: str, image_file) -> dict[str, Any] | None:
    """Image-based disease detection via multipart upload."""
    files = {"image": (image_file.name, image_file, image_file.type)}
    data = {"crop": crop, "symptoms": symptoms}
    return _post_api_file("/chat/disease-detect-upload", files=files, data=data)


# ═══════════════════════════════════════════════════════════════════
# PLANIFICATION
# ═══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def get_roadmap() -> pd.DataFrame:
    """Fetches the seasonal planification roadmap."""
    if USE_MOCK_DATA:
        return mock_data.generate_mock_roadmap()

    zones = _get_api("/segmentation/zones")
    if zones and len(zones) > 0:
        zone_id = zones[0].get("id")
        plans = _get_api(f"/planification/plans/{zone_id}")
        if plans and isinstance(plans, list) and len(plans) > 0:
            roadmap_json = plans[0].get("roadmap_json", [])
            if roadmap_json:
                mapped = [
                    {
                        "Task": step.get("task", "Unknown"),
                        "Start": step.get("start_date", "2026-01-01"),
                        "End": step.get("end_date", "2026-01-31"),
                        "Phase": step.get("phase", "Execution"),
                    }
                    for step in roadmap_json
                ]
                if mapped:
                    return pd.DataFrame(mapped)

    return mock_data.generate_mock_roadmap()


@st.cache_data(ttl=300, show_spinner=False)
def get_zone_resources(zone_id: int) -> dict[str, Any] | None:
    """Resource estimates for a zone."""
    return _get_api(f"/planification/resources/{zone_id}")


def create_roadmap(payload: dict[str, Any]) -> dict[str, Any] | None:
    """POST /planification/roadmap to create a roadmap."""
    return _post_api("/planification/roadmap", payload)


@st.cache_data(ttl=300, show_spinner=False)
def get_zone_plans(zone_id: int) -> list[dict[str, Any]]:
    """Returns saved plans for a zone."""
    data = _get_api(f"/planification/plans/{zone_id}")
    if data and isinstance(data, list):
        return data
    return []


def create_disease_plan(payload: dict[str, Any]) -> dict[str, Any] | None:
    """POST /planification/disease-plan."""
    return _post_api("/planification/disease-plan", payload)


# ═══════════════════════════════════════════════════════════════════
# COMMUNICATION
# ═══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def get_alerts() -> list[dict[str, str]]:
    """Fetches recent communication alerts."""
    if USE_MOCK_DATA:
        return mock_data.generate_mock_alerts()

    alerts = _get_api("/communication/alerts")
    if alerts and isinstance(alerts, list):
        mapped = [
            {
                "type": "Warning" if a.get("is_urgent") else "Info",
                "message": a.get("message", ""),
                "timestamp": str(a.get("created_at", ""))[:10],
            }
            for a in alerts
        ]
        if mapped:
            return mapped

    return mock_data.generate_mock_alerts()


def send_alert(message: str, target_group: str, is_urgent: bool) -> bool:
    """Sends a new communication alert."""
    if USE_MOCK_DATA:
        return True

    url = f"{API_BASE_URL}/communication/alerts"
    payload = {
        "message": message,
        "target_group": target_group,
        "is_urgent": is_urgent,
        "created_by": "System",
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        get_alerts.clear()
        return True
    except Exception as e:
        logger.error("Error sending alert to %s: %s", url, e)
        return False


def send_contact_message(name: str, email: str, subject: str, message: str) -> bool:
    """Simulates sending a contact message."""
    payload = {"name": name, "email": email, "subject": subject, "message": message}
    logger.info("Simulating contact message: %s", payload)
    return True


def notify(payload: dict[str, Any]) -> dict[str, Any] | None:
    """POST /communication/notify."""
    return _post_api("/communication/notify", payload)


@st.cache_data(ttl=300, show_spinner=False)
def get_shared_plan(plan_id: int) -> dict[str, Any] | None:
    """GET /communication/share/{plan_id}."""
    return _get_api(f"/communication/share/{plan_id}")


# ═══════════════════════════════════════════════════════════════════
# LIVE DATA
# ═══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=120, show_spinner=False)
def get_weather(district: str) -> dict[str, Any] | None:
    """Live weather data for a district."""
    return _get_api(f"/live/weather/{district}")


def submit_field_report(payload: dict[str, Any]) -> dict[str, Any] | None:
    """POST /live/field-report."""
    return _post_api("/live/field-report", payload)


@st.cache_data(ttl=120, show_spinner=False)
def get_field_reports(zone_id: int) -> list[dict[str, Any]]:
    """GET /live/field-reports/{zone_id}."""
    data = _get_api(f"/live/field-reports/{zone_id}")
    if data and isinstance(data, list):
        return data
    return []


def get_live_context(payload: dict[str, Any]) -> dict[str, Any] | None:
    """POST /live/context."""
    return _post_api("/live/context", payload)


# ═══════════════════════════════════════════════════════════════════
# ADMIN
# ═══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=60, show_spinner=False)
def get_admin_zones() -> list[dict[str, Any]]:
    """GET /admin/zones — zone management list."""
    data = _get_api("/admin/zones")
    if data and isinstance(data, list):
        return data
    return []


@st.cache_data(ttl=60, show_spinner=False)
def get_admin_plans() -> list[dict[str, Any]]:
    """GET /admin/plans — plan management list."""
    data = _get_api("/admin/plans")
    if data and isinstance(data, list):
        return data
    return []


@st.cache_data(ttl=60, show_spinner=False)
def get_admin_alerts() -> list[dict[str, Any]]:
    """GET /admin/alerts — alert management list."""
    data = _get_api("/admin/alerts")
    if data and isinstance(data, list):
        return data
    return []


@st.cache_data(ttl=60, show_spinner=False)
def get_health() -> dict[str, Any] | None:
    """GET /health — system health check."""
    return _get_api("/health")
