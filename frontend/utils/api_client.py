"""
Extended API client methods for agrimenya frontend.

Covers all backend modules documented in the frontend handoff:
- Decision, Segmentation, Alignment, Chat/AI, Planning, Communication, Live Data, Admin.
"""
import logging
from typing import Any
from urllib.parse import quote, urlencode

import requests
import streamlit as st

from .config import ADMIN_API_KEY, API_BASE_URL, USE_MOCK_DATA, USER_API_KEY
from . import mock_data

logger = logging.getLogger(__name__)


def _user_headers() -> dict[str, str]:
    return {"X-API-Key": USER_API_KEY} if USER_API_KEY else {}


# ── Internal helpers ─────────────────────────────────────────────────

def _get_api(path: str, timeout: int = 10, params: dict[str, Any] | None = None) -> dict[str, Any] | list[Any] | None:
    """GET request to the FastAPI backend, returns parsed JSON or None."""
    url = f"{API_BASE_URL}{path}"
    if params:
        url = f"{url}?{urlencode({k: v for k, v in params.items() if v is not None}, doseq=True)}"
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error("API GET %s failed: %s", url, e)
        return None


def _post_api(path: str, payload: dict | None = None, timeout: int = 15, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """POST request to the FastAPI backend, returns parsed JSON or None."""
    url = f"{API_BASE_URL}{path}"
    if params:
        url = f"{url}?{urlencode({k: v for k, v in params.items() if v is not None}, doseq=True)}"
    try:
        resp = requests.post(url, json=payload or {}, headers=_user_headers(), timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error("API POST %s failed: %s", url, e)
        return None


def _post_api_file(path: str, files: dict, data: dict | None = None, timeout: int = 30) -> dict[str, Any] | None:
    """POST multipart/form-data to the FastAPI backend."""
    url = f"{API_BASE_URL}{path}"
    try:
        resp = requests.post(url, files=files, data=data or {}, headers=_user_headers(), timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error("API POST (file) %s failed: %s", url, e)
        return None


def _admin_headers() -> dict[str, str]:
    return {"X-Admin-Key": ADMIN_API_KEY} if ADMIN_API_KEY else {}


# ═══════════════════════════════════════════════════════════════════
# DASHBOARD / KPIs
# ═══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def get_kpis() -> dict[str, Any]:
    """Return only overview metrics backed by live API data."""
    if USE_MOCK_DATA:
        zones = mock_data.generate_mock_zones()
        return {"total_zones": len(zones), "baseline_yield_kg_ha": None, "active_alerts": None}
    zones = get_zones()
    alerts = get_alerts()
    data = _get_api("/health")
    return {
        "total_zones": len(zones),
        "baseline_yield_kg_ha": data.get("baselines_overall_average") if data else None,
        "active_alerts": len(alerts),
    }


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
    return {}


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
                "predicted_yield": "Production_MT",
                "district": "District",
            }, inplace=True)
            # Saved predictions are total kg for the selected zone area.
            if "Production_MT" in df.columns:
                df["Production_MT"] = pd.to_numeric(df["Production_MT"], errors="coerce") / 1000
            if "Crop" not in df.columns:
                df["Crop"] = df["crop_type"] if "crop_type" in df.columns else "Unknown"
            if "Crop" in df.columns:
                df["Crop"] = df["Crop"].fillna("Unspecified").astype(str)
            if "Priority" in df.columns:
                df["Priority"] = df["Priority"].fillna("Unassessed").astype(str)
            if "District" in df.columns:
                df["District"] = df["District"].fillna("Unknown").astype(str)
            return df

    return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def get_zones() -> list[dict[str, Any]]:
    """Returns all zones from the backend."""
    if USE_MOCK_DATA:
        return mock_data.generate_mock_zones()
    data = _get_api("/segmentation/zones")
    if data and isinstance(data, list):
        map_rows = _get_api("/segmentation/map-data") or []
        map_by_id = {str(row.get("id")): row for row in map_rows if row.get("id")}
        normalized = []
        for zone in data:
            row = {**zone, **map_by_id.get(str(zone.get("id")), {})}
            row["name"] = " / ".join(filter(None, [row.get("district"), row.get("sector"), row.get("cell")])) or str(row.get("id", "Zone"))
            row["crop"] = row.get("crop_type") or row.get("crop") or ""
            row["priority"] = row.get("priority_level") or row.get("priority") or ""
            row["risk_status"] = row.get("climate_risk_level") or row.get("nutrition_risk_level") or "Unknown"
            row["area_ha"] = row.get("area_cultivated")
            row["predicted_production_kg"] = row.get("predicted_yield")
            normalized.append(row)
        return normalized
    return []


@st.cache_data(ttl=300, show_spinner=False)
def get_zone_detail(zone_id: str) -> dict[str, Any] | None:
    """Returns detail for a single zone."""
    data = _get_api(f"/segmentation/zones/{quote(str(zone_id), safe='')}")
    return data


def create_zone(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Create a zone through the backend and refresh cached zone views."""
    result = _post_api("/segmentation/zones", payload)
    if result:
        get_zones.clear()
        get_priority_data.clear()
    return result


@st.cache_data(ttl=300, show_spinner=False)
def get_agri_metrics() -> list[dict[str, Any]]:
    """Returns agri metrics from segmentation."""
    if USE_MOCK_DATA:
        return mock_data.generate_mock_agri_metrics()
    data = _get_api("/segmentation/agri-metrics")
    if data and isinstance(data, list):
        return data
    return []


@st.cache_data(ttl=300, show_spinner=False)
def get_crop_comparison(district: str, season: str | None = None) -> list[dict[str, Any]]:
    """Returns crop comparison for a district."""
    data = _get_api(f"/segmentation/crop-comparison/{quote(district, safe='')}", params={"season": season})
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
            district = (r.get("zones") or {}).get("district", "Unknown")

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
    return []


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


def get_zone_recommendations(zone_id: str) -> dict[str, Any] | None:
    """GET /decision/recommendations/{zone_id}."""
    return _get_api(f"/decision/recommendations/{zone_id}")


# ═══════════════════════════════════════════════════════════════════
# ALIGNMENT
# ═══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def get_finance_readiness(zone_id: str) -> dict[str, Any] | None:
    """Finance readiness for a zone."""
    return _get_api(f"/alignment/finance-readiness/{zone_id}")


@st.cache_data(ttl=300, show_spinner=False)
def get_nutrition_risk(zone_id: str) -> dict[str, Any] | None:
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

def chat(message: str, zone_id: str) -> dict[str, Any] | None:
    """Sends a message to the AI assistant."""
    payload: dict[str, Any] = {"question": message, "zone_id": zone_id}
    # The backend may wait up to 20 seconds for an LLM provider response.
    return _post_api("/chat", payload, timeout=35)


def disease_detect(crop: str, symptoms: str, zone_id: str, image_description: str | None = None) -> dict[str, Any] | None:
    """Text-based disease detection."""
    return _post_api("/chat/disease-detect", {"zone_id": zone_id, "crop": crop, "symptoms": symptoms, "image_description": image_description})


def disease_detect_upload(crop: str, symptoms: str, zone_id: str, image_file, image_description: str | None = None) -> dict[str, Any] | None:
    """Image-based disease detection via multipart upload."""
    files = {"image": (image_file.name, image_file, image_file.type)}
    data = {"zone_id": zone_id, "crop": crop, "symptoms": symptoms}
    if image_description:
        data["image_description"] = image_description
    return _post_api_file("/chat/disease-detect-upload", files=files, data=data)


# ═══════════════════════════════════════════════════════════════════
# PLANIFICATION
# ═══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def get_roadmap(zone_id: str | None = None) -> pd.DataFrame:
    """Fetch the latest saved roadmap for the selected zone."""
    if USE_MOCK_DATA:
        return mock_data.generate_mock_roadmap()

    if zone_id:
        plans = get_zone_plans(zone_id)
        if plans:
            roadmap_json = plans[0].get("roadmap_json", [])
            mapped = [
                {
                    "Task": step.get("title", "Unknown"),
                    "Timeframe": step.get("timeframe", "Not specified"),
                    "Description": step.get("description", ""),
                }
                for step in roadmap_json
            ]
            if mapped:
                return pd.DataFrame(mapped)

    return pd.DataFrame(columns=["Task", "Timeframe", "Description"])


@st.cache_data(ttl=300, show_spinner=False)
def get_zone_resources(zone_id: str, area_cultivated: float | None = None, rainfall_mm: float | None = None) -> dict[str, Any] | None:
    """Resource estimates for a zone."""
    return _get_api(f"/planification/resources/{zone_id}", params={"area_cultivated": area_cultivated, "rainfall_mm": rainfall_mm})


def create_roadmap(payload: dict[str, Any]) -> dict[str, Any] | None:
    """POST /planification/roadmap to create a roadmap."""
    return _post_api("/planification/roadmap", payload)


@st.cache_data(ttl=300, show_spinner=False)
def get_zone_plans(zone_id: str) -> list[dict[str, Any]]:
    """Returns saved plans for a zone."""
    data = _get_api(f"/planification/plans/{zone_id}")
    if data and isinstance(data, list):
        return data
    return []


def create_disease_plan(payload: dict[str, Any]) -> dict[str, Any] | None:
    """POST /planification/disease-plan."""
    params = {key: payload.get(key) for key in ("zone_id", "crop", "symptoms", "image_description")}
    return _post_api("/planification/disease-plan", params=params)


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
            "type": a.get("severity", "Info"),
                "message": a.get("message", ""),
                "timestamp": str(a.get("created_at", ""))[:10],
            }
            for a in alerts
        ]
        if mapped:
            return mapped

    return []


def send_alert(message: str, zone_id: str, severity: str) -> dict[str, Any] | None:
    """Sends a new communication alert."""
    if USE_MOCK_DATA:
        return None

    url = f"{API_BASE_URL}/communication/alerts"
    payload = {
        "zone_id": zone_id,
        "message": message,
        "severity": severity,
        "created_by": "System",
    }
    try:
        resp = requests.post(url, json=payload, headers=_user_headers(), timeout=10)
        resp.raise_for_status()
        get_alerts.clear()
        return resp.json()
    except Exception as e:
        logger.error("Error sending alert to %s: %s", url, e)
        return False


def send_contact_message(name: str, email: str, subject: str, message: str) -> bool:
    """Send a contact message to the backend's configured support inbox."""
    result = _post_api(
        "/communication/contact",
        {"name": name, "email": email, "subject": subject, "message": message},
    )
    return bool(result and result.get("status") == "sent")


def notify(payload: dict[str, Any]) -> dict[str, Any] | None:
    """POST /communication/notify."""
    return _post_api("/communication/notify", payload)


@st.cache_data(ttl=300, show_spinner=False)
def get_shared_plan(plan_id: str) -> dict[str, Any] | None:
    """GET /communication/share/{plan_id}."""
    return _get_api(f"/communication/share/{plan_id}")


# ═══════════════════════════════════════════════════════════════════
# LIVE DATA
# ═══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=120, show_spinner=False)
def get_weather(district: str) -> dict[str, Any] | None:
    """Live weather data for a district."""
    return _get_api(f"/live/weather/{quote(district, safe='')}")


def submit_field_report(payload: dict[str, Any]) -> dict[str, Any] | None:
    """POST /live/field-report."""
    return _post_api("/live/field-report", payload)


@st.cache_data(ttl=120, show_spinner=False)
def get_field_reports(zone_id: int) -> list[dict[str, Any]]:
    """GET /live/field-reports/{zone_id}."""
    data = _get_api(f"/live/field-reports/{quote(str(zone_id), safe='')}")
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
    data = _request_admin("GET", "/admin/zones")
    if data and isinstance(data, list):
        return data
    return []


@st.cache_data(ttl=60, show_spinner=False)
def get_admin_plans() -> list[dict[str, Any]]:
    """GET /admin/plans — plan management list."""
    data = _request_admin("GET", "/admin/plans")
    if data and isinstance(data, list):
        return data
    return []


@st.cache_data(ttl=60, show_spinner=False)
def get_admin_alerts() -> list[dict[str, Any]]:
    """GET /admin/alerts — alert management list."""
    data = _request_admin("GET", "/admin/alerts")
    if data and isinstance(data, list):
        return data
    return []


@st.cache_data(ttl=60, show_spinner=False)
def get_health() -> dict[str, Any] | None:
    """GET /health — system health check."""
    return _get_api("/health")


def _request_admin(method: str, path: str) -> Any:
    if not ADMIN_API_KEY:
        logger.info("Admin API key is not configured; skipping %s", path)
        return None
    try:
        response = requests.request(method, f"{API_BASE_URL}{path}", headers=_admin_headers(), timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        logger.error("Admin API %s %s failed: %s", method, path, exc)
        return None
