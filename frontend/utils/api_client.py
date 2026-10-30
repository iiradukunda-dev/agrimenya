"""
Extended API client methods for agrimenya frontend.

Covers all backend modules documented in the frontend handoff:
- Decision, Segmentation, Alignment, Chat/AI, Planning, Communication, Live Data, Admin.
"""
import logging
import time
from typing import Any
from urllib.parse import quote, urlencode, urlparse

import requests
import streamlit as st

from .config import API_BASE_URL, USE_MOCK_DATA, USER_API_KEY
from . import mock_data

logger = logging.getLogger(__name__)
ADMIN_SESSION_SECONDS = 30 * 60


def _authenticate_admin_session(widget_key: str) -> None:
    email_key = widget_key.removesuffix("_password") + "_email"
    email = st.session_state.get(email_key, "").strip()
    password = st.session_state.pop(widget_key, "")
    if not email or not password:
        st.session_state["admin_login_error"] = "Enter both your administrator email and password."
        return
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/admin/login",
            json={"email": email, "password": password}, timeout=15,
        )
        response.raise_for_status()
        result = response.json()
        st.session_state["admin_access_token"] = result["access_token"]
        st.session_state["admin_session_expires_at"] = time.monotonic() + int(result.get("expires_in", ADMIN_SESSION_SECONDS))
        st.session_state["admin_identity"] = result.get("admin", {})
        st.session_state.pop("admin_login_error", None)
    except requests.RequestException as exc:
        detail = None
        if exc.response is not None:
            try:
                body = exc.response.json()
                detail = body.get("detail") if isinstance(body, dict) else None
            except (ValueError, AttributeError):
                pass
        if isinstance(detail, list):
            detail = "Enter both your administrator email and password."
        st.session_state["admin_login_error"] = str(detail or "Sign-in failed. Check the API connection and your credentials.")


def admin_session_authenticated() -> bool:
    expires = st.session_state.get("admin_session_expires_at", 0)
    if expires <= time.monotonic() or not st.session_state.get("admin_access_token"):
        st.session_state.pop("admin_session_expires_at", None)
        st.session_state.pop("admin_access_token", None)
        st.session_state.pop("admin_identity", None)
        return False
    return True


def admin_sign_out() -> None:
    """Sign out the current administrator session."""
    st.session_state.pop("admin_session_expires_at", None)
    st.session_state.pop("admin_access_token", None)
    st.session_state.pop("admin_identity", None)
    st.session_state.pop("admin_login_error", None)
    st.session_state.pop("admin_api_errors", None)


def render_admin_login(key_prefix: str = "admin") -> bool:
    """Require a named administrator account before using admin APIs."""
    from components.cards import render_centralized_login_card

    return render_centralized_login_card(portal="admin", key_prefix=key_prefix)


def request_admin_password_reset(email: str) -> bool:
    return _request_public_admin_auth("/auth/admin/password/forgot", {"email": email}) is not None


def reset_admin_password(token: str, new_password: str) -> dict[str, Any] | None:
    return _request_public_admin_auth(
        "/auth/admin/password/reset", {"token": token, "new_password": new_password}
    )


def _request_public_admin_auth(path: str, payload: dict[str, str]) -> dict[str, Any] | None:
    try:
        response = requests.post(f"{API_BASE_URL}{path}", json=payload, timeout=15)
        response.raise_for_status()
        errors = dict(st.session_state.get("admin_api_errors", {}))
        errors.pop(path, None)
        st.session_state["admin_api_errors"] = errors
        return response.json()
    except requests.RequestException as exc:
        detail = None
        response = exc.response
        if response is not None:
            try:
                body = response.json()
                detail = body.get("detail") if isinstance(body, dict) else None
            except (ValueError, AttributeError):
                pass
            if isinstance(detail, list):
                messages = [str(item.get("msg")) for item in detail if isinstance(item, dict) and item.get("msg")]
                detail = "; ".join(messages) if messages else None
            if not detail:
                detail = f"The administrator auth endpoint returned HTTP {response.status_code}."
        else:
            logger.warning("Admin auth request %s failed with %s", path, type(exc).__name__)
            api_host = urlparse(API_BASE_URL).hostname or "the configured API host"
            detail = f"Could not reach the backend at {api_host} ({type(exc).__name__})."
        errors = dict(st.session_state.get("admin_api_errors", {}))
        errors[path] = str(detail)
        st.session_state["admin_api_errors"] = errors
        return None


def _user_headers() -> dict[str, str]:
    return {"X-API-Key": USER_API_KEY} if USER_API_KEY else {}


# ── Internal helpers ─────────────────────────────────────────────────

def _get_api(path: str, timeout: int = 10, params: dict[str, Any] | None = None) -> dict[str, Any] | list[Any] | None:
    """GET request to the FastAPI backend, returns parsed JSON or None."""
    url = f"{API_BASE_URL}{path}"
    if params:
        url = f"{url}?{urlencode({k: v for k, v in params.items() if v is not None}, doseq=True)}"
    try:
        resp = requests.get(url, headers=_user_headers(), timeout=timeout)
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


def _put_api(path: str, payload: dict[str, Any], timeout: int = 15) -> dict[str, Any] | None:
    """PUT request to the API using the configured user credential."""
    try:
        resp = requests.put(f"{API_BASE_URL}{path}", json=payload, headers=_user_headers(), timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error("API PUT %s failed: %s", path, e)
        return None


def _patch_api(path: str, payload: dict[str, Any] | None = None, timeout: int = 15) -> dict[str, Any] | None:
    """PATCH request to the FastAPI backend, returns parsed JSON or None."""
    url = f"{API_BASE_URL}{path}"
    try:
        resp = requests.patch(url, json=payload or {}, headers=_user_headers(), timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error("API PATCH %s failed: %s", url, e)
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
    token = st.session_state.get("admin_access_token", "")
    return {"Authorization": f"Bearer {token}"} if token else {}


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
        "baseline_yield_kg_ha": data.get("baselines_overall_average") if isinstance(data, dict) else None,
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
    if isinstance(data, dict):
        return data
    return {}


# ═══════════════════════════════════════════════════════════════════
# SEGMENTATION
# ═══════════════════════════════════════════════════════════════════

# pandas imported lazily in dataframe methods


@st.cache_data(ttl=300, show_spinner=False)
def get_priority_data() -> Any:
    """Segmentation map data for prioritizing agricultural zones."""
    import pandas as pd
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
                df["Production_MT"] = pd.Series(pd.to_numeric(df["Production_MT"], errors="coerce"), dtype=float) / 1000.0
            if "Crop" not in df.columns:
                df["Crop"] = df["crop_type"] if "crop_type" in df.columns else "Unknown"
            if "Crop" in df.columns:
                df["Crop"] = df["Crop"].fillna("Unspecified").astype(str)
            if "Priority" in df.columns:
                df["Priority"] = df["Priority"].fillna("Unassessed").astype(str)
            if "District" in df.columns:
                df["District"] = df["District"].fillna("Unknown").astype(str)
            return df

    return pd.DataFrame(data=[])


@st.cache_data(ttl=300, show_spinner=False)
def get_zones() -> list[dict[str, Any]]:
    """Returns all zones from the backend."""
    if USE_MOCK_DATA:
        return mock_data.generate_mock_zones()
    data = _get_api("/segmentation/zones")
    if data and isinstance(data, list):
        map_resp = _get_api("/segmentation/map-data")
        map_rows = map_resp if isinstance(map_resp, list) else []
        map_by_id = {
            str(row.get("id")): row
            for row in map_rows
            if isinstance(row, dict) and row.get("id")
        }
        normalized = []
        for zone in data:
            if not isinstance(zone, dict):
                continue
            matching = map_by_id.get(str(zone.get("id")), {})
            row = {**zone, **matching}
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
    data = _get_api(f"/segmentation/zones/{quote(zone_id, safe='')}")
    return data if isinstance(data, dict) else None


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


@st.cache_data(ttl=3600, show_spinner=False)
def get_official_yields() -> list[dict[str, Any]]:
    """Return bundled district-level NISR yield observations across available seasons."""
    data = _get_api("/segmentation/official-yields", timeout=20)
    return data if isinstance(data, list) else []


@st.cache_data(ttl=3600, show_spinner=False)
def get_districts() -> list[dict[str, Any]]:
    """Return the canonical district directory used by maps and weather views."""
    data = _get_api("/segmentation/districts")
    return data if isinstance(data, list) else []


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
def get_model_info() -> dict[str, Any] | None:
    """GET /decision/model-info: yield prediction baseline model metadata and provenance."""
    if USE_MOCK_DATA:
        return mock_data.generate_mock_model_info()
    data = _get_api("/decision/model-info")
    if isinstance(data, dict):
        return data
    return mock_data.generate_mock_model_info()


@st.cache_data(ttl=300, show_spinner=False)
def get_district_ranking(crop: str, season: str | None = None) -> list[dict[str, Any]]:
    """GET /decision/district-ranking: district yield benchmarking against national reference."""
    if USE_MOCK_DATA:
        return mock_data.generate_mock_district_ranking(crop=crop, season=season)
    params = {"crop": crop}
    if season:
        params["season"] = season
    data = _get_api("/decision/district-ranking", params=params)
    if isinstance(data, list):
        return data
    return mock_data.generate_mock_district_ranking(crop=crop, season=season)


@st.cache_data(ttl=300, show_spinner=False)
def get_evidence_ranking(crop: str, season: str | None = None) -> dict[str, Any] | None:
    """GET /decision/evidence-ranking: national reference, observations, and ranked districts."""
    params = {"crop": crop}
    if season:
        params["season"] = season
    data = _get_api("/decision/evidence-ranking", params=params)
    return data if isinstance(data, dict) else None


def get_disease_risk(zone_id: str, crop: str, symptoms: str, image_description: str | None = None) -> dict[str, Any] | None:
    """POST /decision/disease-risk: evaluate agronomic risk and recommended actions."""
    params = {
        "zone_id": zone_id,
        "crop": crop,
        "symptoms": symptoms,
    }
    if image_description:
        params["image_description"] = image_description
    return _post_api("/decision/disease-risk", params=params)


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

            rec_data = _get_api(f"/decision/recommendations/{quote(str(zone_id), safe='')}")
            texts = rec_data.get("recommendations", []) if isinstance(rec_data, dict) else []
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
    data = _get_api(f"/decision/recommendations/{quote(zone_id, safe='')}")
    return data if isinstance(data, dict) else None


# ═══════════════════════════════════════════════════════════════════
# ALIGNMENT
# ═══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def get_finance_readiness(zone_id: str) -> dict[str, Any] | None:
    """Finance readiness for a zone."""
    data = _get_api(f"/alignment/finance-readiness/{quote(zone_id, safe='')}")
    return data if isinstance(data, dict) else None


@st.cache_data(ttl=300, show_spinner=False)
def get_nutrition_risk(zone_id: str) -> dict[str, Any] | None:
    """Nutrition risk assessment for a zone."""
    data = _get_api(f"/alignment/nutrition-risk/{quote(zone_id, safe='')}")
    return data if isinstance(data, dict) else None


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
def get_roadmap(zone_id: str | None = None) -> Any:
    """Fetch the latest saved roadmap for the selected zone."""
    import pandas as pd
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

    return pd.DataFrame(data={"Task": [], "Timeframe": [], "Description": []})


@st.cache_data(ttl=300, show_spinner=False)
def get_zone_resources(zone_id: str, **inputs: float | None) -> dict[str, Any] | None:
    """Resource estimates for a zone."""
    data = _get_api(f"/planification/resources/{quote(zone_id, safe='')}", params=inputs)
    return data if isinstance(data, dict) else None


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


def update_plan_action_status(plan_id: str, step_number: int, status: str, change_note: str = "") -> dict[str, Any] | None:
    """PATCH /planification/plans/{plan_id}/actions/{step_number}."""
    payload = {"status": status, "change_note": change_note.strip()}
    return _patch_api(f"/planification/plans/{quote(plan_id, safe='')}/actions/{step_number}", payload)



def get_seasonal_plan_draft(zone_id: str, crop: str) -> dict[str, Any] | None:
    """GET /planification/draft returns an agro-ecological seasonal draft with planting windows and phases."""
    params = {"zone_id": zone_id, "crop": crop.strip()}
    data = _get_api("/planification/draft", params=params)
    return data if isinstance(data, dict) else None


def estimate_resources_advanced(zone_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    """POST /planification/resources/{zone_id}/estimate for dynamic fertilizer, seed, and input pricing."""
    return _post_api(f"/planification/resources/{quote(zone_id, safe='')}/estimate", payload)


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


def send_alert(message: str, zone_id: str, severity: str, crop: str | None = None, action: str | None = None) -> dict[str, Any] | None:
    """Sends a new communication alert with automatic email broadcast."""
    if USE_MOCK_DATA:
        return None

    url = f"{API_BASE_URL}/communication/alerts"
    payload = {
        "zone_id": zone_id,
        "message": message,
        "severity": severity,
        "created_by": "Agrimenya Portal",
    }
    if crop:
        payload["crop"] = crop
    if action:
        payload["action"] = action

    try:
        headers = _admin_headers() if admin_session_authenticated() else _user_headers()
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        get_alerts.clear()
        return resp.json()
    except Exception as e:
        logger.error("Error sending alert to %s: %s", url, e)
        return None


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
    data = _get_api(f"/communication/share/{quote(plan_id, safe='')}")
    return data if isinstance(data, dict) else None


def send_shared_plan(plan_id: str, email: str) -> dict[str, Any] | None:
    """POST /communication/share/{plan_id}/send: email formatted plan to farmer or officer."""
    return _post_api(f"/communication/share/{quote(plan_id, safe='')}/send", {"email": email})


@st.cache_data(ttl=120, show_spinner=False)
def get_email_status() -> dict[str, Any] | None:
    """GET /communication/email-status: check if SMTP email delivery is operational."""
    data = _get_api("/communication/email-status")
    return data if isinstance(data, dict) else None


@st.cache_data(ttl=120, show_spinner=False)
def get_whatsapp_status_info() -> dict[str, Any] | None:
    """GET /communication/whatsapp-status: check WhatsApp provider readiness."""
    data = _get_api("/communication/whatsapp-status")
    return data if isinstance(data, dict) else None



def get_whatsapp_contacts() -> list[dict[str, Any]]:
    """List WhatsApp contacts using the admin-only endpoint."""
    data = _request_admin("GET", "/communication/contacts?limit=200")
    return data if isinstance(data, list) else []


def get_whatsapp_health() -> dict[str, Any] | None:
    return _request_admin("GET", "/communication/whatsapp/health")


def get_whatsapp_stats() -> dict[str, Any] | None:
    return _request_admin("GET", "/communication/whatsapp/stats")


def get_whatsapp_templates() -> list[dict[str, Any]]:
    data = _request_admin("GET", "/communication/whatsapp/templates")
    return data if isinstance(data, list) else []


def preview_whatsapp_template(name: str, language: str, params: list[str]) -> dict[str, Any] | None:
    path = (
        f"/communication/whatsapp/templates/{quote(name, safe='')}/"
        f"{quote(language, safe='')}/preview"
    )
    return _request_admin("POST", path, {"params": params})


def create_whatsapp_contact(payload: dict[str, Any]) -> dict[str, Any] | None:
    result = _request_admin("POST", "/communication/contacts", payload)
    return result


def opt_in_whatsapp_contact(contact_id: str, source: str, text_version: str) -> dict[str, Any] | None:
    result = _request_admin(
        "POST", f"/communication/contacts/{quote(contact_id, safe='')}/opt-in",
        {"source": source, "text_version": text_version},
    )
    return result


def subscribe_whatsapp_contact(contact_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    return _request_admin(
        "POST", f"/communication/contacts/{quote(contact_id, safe='')}/subscriptions", payload,
    )


def remove_whatsapp_contact(contact_id: str) -> dict[str, Any] | None:
    result = _request_admin("DELETE", f"/communication/contacts/{quote(contact_id, safe='')}")
    return result


def approve_whatsapp_alert(alert_id: str) -> dict[str, Any] | None:
    result = _request_admin("POST", f"/communication/alerts/{quote(alert_id, safe='')}/approve")
    return result


def dispatch_whatsapp_alert(alert_id: str) -> dict[str, Any] | None:
    return _request_admin("POST", f"/communication/alerts/{quote(alert_id, safe='')}/dispatch/whatsapp")


def get_whatsapp_delivery(alert_id: str) -> dict[str, Any] | None:
    return _request_admin("GET", f"/communication/alerts/{quote(alert_id, safe='')}/delivery")


# ═══════════════════════════════════════════════════════════════════
# LIVE DATA
# ═══════════════════════════════════════════════════════════════════

RWANDA_DISTRICT_COORDS: dict[str, tuple[float, float]] = {
    "gasabo": (-1.9346, 30.1044),
    "kicukiro": (-1.9878, 30.1044),
    "nyarugenge": (-1.9536, 30.0605),
    "kigali city": (-1.9441, 30.0619),
    "gisagara": (-2.5833, 29.8333),
    "huye": (-2.5967, 29.7392),
    "kamonyi": (-2.0333, 29.8833),
    "muhanga": (-2.0833, 29.7500),
    "nyamagabe": (-2.4667, 29.4667),
    "nyanza": (-2.3500, 29.7500),
    "nyaruguru": (-2.6167, 29.5667),
    "ruhango": (-2.2167, 29.7833),
    "karongi": (-2.0000, 29.3833),
    "ngororero": (-1.8667, 29.5667),
    "nyabihu": (-1.6500, 29.5000),
    "nyamasheke": (-2.3500, 29.1333),
    "rubavu": (-1.6789, 29.2661),
    "rusizi": (-2.4846, 28.9075),
    "rutsiro": (-1.8833, 29.3333),
    "burera": (-1.4667, 29.8667),
    "gakenke": (-1.6833, 29.7833),
    "gicumbi": (-1.5667, 30.1000),
    "musanze": (-1.4995, 29.6335),
    "rulindo": (-1.7500, 30.0333),
    "bugesera": (-2.2167, 30.2500),
    "gatsibo": (-1.6000, 30.4667),
    "kayonza": (-1.8833, 30.5333),
    "kirehe": (-2.2500, 30.7833),
    "ngoma": (-2.1667, 30.5333),
    "nyagatare": (-1.2947, 30.3250),
    "rwamagana": (-1.9487, 30.4347),
}


def _fetch_direct_open_meteo(district: str) -> dict[str, Any] | None:
    norm = district.strip().lower()
    coords = RWANDA_DISTRICT_COORDS.get(norm)
    if coords is None:
        logger.warning("Cannot fetch weather for unknown district %s", district)
        return None
    try:
        resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": coords[0],
                "longitude": coords[1],
                "current": "temperature_2m,relative_humidity_2m,precipitation,rain,wind_speed_10m,weather_code",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum",
                "wind_speed_unit": "kmh",
                "forecast_days": 5,
                "timezone": "auto",
            },
            timeout=8,
        )
        resp.raise_for_status()
        payload = resp.json()
        current = payload.get("current", {})
        daily = payload.get("daily", {})
        forecast = [
            {
                "date": date,
                "temperature_max_c": daily.get("temperature_2m_max", [])[i],
                "temperature_min_c": daily.get("temperature_2m_min", [])[i],
                "precipitation_probability_pct": daily.get("precipitation_probability_max", [])[i],
                "precipitation_sum_mm": daily.get("precipitation_sum", [])[i],
            }
            for i, date in enumerate(daily.get("time", []))
            if all(i < len(daily.get(key, [])) for key in (
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_probability_max",
                "precipitation_sum",
            ))
        ]
        temp = current.get("temperature_2m")
        hum = current.get("relative_humidity_2m")
        precip = current.get("precipitation") if current.get("precipitation") is not None else current.get("rain", 0.0)
        wind = current.get("wind_speed_10m")
        return {
            "district": district,
            "source": "Open-Meteo Live API",
            "latitude": coords[0],
            "longitude": coords[1],
            "temperature_c": temp,
            "humidity_pct": hum,
            "rainfall_mm": precip,
            "wind_kph": wind,
            "weather_code": current.get("weather_code"),
            "summary": f"Live weather snapshot for {district}",
            "updated_at": current.get("time") or time.strftime("%Y-%m-%d %H:%M"),
            "forecast": forecast,
        }
    except Exception as exc:
        logger.warning("Direct Open-Meteo weather fetch failed for %s: %s", district, exc)
        return None


@st.cache_data(ttl=120, show_spinner=False)
def get_weather(district: str) -> dict[str, Any] | None:
    """Live weather data for a district with seamless backend & direct Open-Meteo fallback."""
    data = None
    try:
        data = _get_api(f"/live/weather/{quote(district, safe='')}", timeout=5)
    except Exception:
        data = None

    if isinstance(data, dict) and data.get("temperature_c") is not None:
        return data

    direct = _fetch_direct_open_meteo(district)
    if direct:
        return direct

    return data if isinstance(data, dict) else {
        "district": district,
        "source": "unavailable",
        "temperature_c": None,
        "humidity_pct": None,
        "rainfall_mm": None,
        "wind_kph": None,
        "summary": "Weather data temporarily unavailable",
        "updated_at": None,
        "forecast": [],
    }


def submit_field_report(payload: dict[str, Any]) -> dict[str, Any] | None:
    """POST /live/field-report."""
    return _post_api("/live/field-report", payload)


@st.cache_data(ttl=120, show_spinner=False)
def get_field_reports(zone_id: str) -> list[dict[str, Any]]:
    """GET /live/field-reports/{zone_id}."""
    data = _get_api(f"/live/field-reports/{quote(zone_id, safe='')}")
    if data and isinstance(data, list):
        return data
    return []


@st.cache_data(ttl=60, show_spinner=False)
def get_field_risk(zone_id: str, crop: str | None = None) -> dict[str, Any] | None:
    """Recent community observation summary for decision context."""
    suffix = f"?crop={quote(crop, safe='')}" if crop else ""
    data = _get_api(f"/live/field-risk/{quote(zone_id, safe='')}{suffix}")
    return data if isinstance(data, dict) else None


@st.cache_data(ttl=120, show_spinner=False)
def get_zone_readiness(zone_id: str) -> dict[str, Any] | None:
    """GET /alignment/readiness/{zone_id}."""
    data = _get_api(f"/alignment/readiness/{quote(zone_id, safe='')}")
    return data if isinstance(data, dict) else None


def update_zone_readiness(zone_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    """PUT /alignment/readiness/{zone_id}."""
    result = _put_api(f"/alignment/readiness/{quote(zone_id, safe='')}", payload)
    if result:
        get_zone_readiness.clear()
    return result


@st.cache_data(ttl=120, show_spinner=False)
def get_zone_work_records(zone_id: str) -> list[dict[str, Any]]:
    """GET /alignment/work-records/{zone_id}."""
    data = _get_api(f"/alignment/work-records/{quote(zone_id, safe='')}")
    return data if isinstance(data, list) else []


def create_zone_work_record(zone_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    """POST /alignment/work-records/{zone_id} and refresh affected dashboard totals."""
    result = _post_api(f"/alignment/work-records/{quote(zone_id, safe='')}", payload)
    if result:
        get_zone_work_records.clear()
        get_alignment_dashboard.clear()
    return result


def get_live_context(payload: dict[str, Any]) -> dict[str, Any] | None:
    """POST /live/context."""
    return _post_api("/live/context", payload)


# ═══════════════════════════════════════════════════════════════════
# ADMIN
# ═══════════════════════════════════════════════════════════════════

def get_admin_zones() -> list[dict[str, Any]]:
    """GET /admin/zones: zone management list."""
    data = _request_admin("GET", "/admin/zones")
    if data and isinstance(data, list):
        return data
    return []


def get_admin_plans() -> list[dict[str, Any]]:
    """GET /admin/plans: plan management list."""
    data = _request_admin("GET", "/admin/plans")
    if data and isinstance(data, list):
        return data
    return []


def get_admin_alerts() -> list[dict[str, Any]]:
    """GET /admin/alerts: alert management list."""
    data = _request_admin("GET", "/admin/alerts")
    if data and isinstance(data, list):
        return data
    return []


def send_admin_alert(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Create an alert and broadcast it to active farmer-community email accounts."""
    result = _request_admin("POST", "/communication/alerts", payload, timeout=120)
    if result:
        get_alerts.clear()
    return result


def get_admin_api_error(path: str) -> str | None:
    """Return the latest safe error detail for an admin request path."""
    errors = st.session_state.get("admin_api_errors", {})
    return errors.get(path)


def get_admin_accounts() -> list[dict[str, Any]]:
    data = _request_admin("GET", "/auth/admin/accounts")
    return data if isinstance(data, list) else []


def get_community_moderation_reports() -> list[dict[str, Any]]:
    data = _request_admin("GET", "/community/moderation/reports")
    return data if isinstance(data, list) else []


def get_community_moderation_posts() -> list[dict[str, Any]]:
    data = _request_admin("GET", "/community/moderation/posts")
    return data if isinstance(data, list) else []


def get_community_moderation_field_reports() -> list[dict[str, Any]]:
    data = _request_admin("GET", "/community/moderation/field-reports")
    return data if isinstance(data, list) else []


def delete_community_field_report(report_id: str) -> dict[str, Any] | None:
    return _request_admin("DELETE", f"/community/moderation/field-reports/{quote(report_id, safe='')}")


def moderate_community_content(payload: dict[str, Any]) -> dict[str, Any] | None:
    return _request_admin("PATCH", "/community/moderation", payload)


def get_community_accounts() -> list[dict[str, Any]]:
    data = _request_admin("GET", "/community/moderation/accounts")
    return data if isinstance(data, list) else []


def set_community_account_active(account_id: str, is_active: bool) -> dict[str, Any] | None:
    return _request_admin("PATCH", f"/community/moderation/accounts/{quote(account_id, safe='')}/status",
                          {"is_active": is_active})


def invite_admin_account(email: str, display_name: str) -> dict[str, Any] | None:
    return _request_admin("POST", "/auth/admin/accounts", {"email": email, "display_name": display_name})


def set_admin_account_active(account_id: str, is_active: bool) -> dict[str, Any] | None:
    return _request_admin(
        "PATCH", f"/auth/admin/accounts/{quote(account_id, safe='')}/status", {"is_active": is_active}
    )


def update_admin_zone(zone_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    result = _request_admin("PATCH", f"/admin/zones/{quote(zone_id, safe='')}", payload)
    if result:
        get_zones.clear()
        get_priority_data.clear()
    return result


def update_admin_plan(plan_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    result = _request_admin("PATCH", f"/admin/plans/{quote(plan_id, safe='')}", payload)
    if result:
        get_zone_plans.clear()
        get_roadmap.clear()
    return result


def update_admin_alert(alert_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    result = _request_admin("PATCH", f"/admin/alerts/{quote(alert_id, safe='')}", payload)
    if result:
        get_alerts.clear()
    return result


def approve_admin_alert(alert_id: str) -> dict[str, Any] | None:
    """Approve an alert for broadcast dispatch."""
    result = _request_admin("POST", f"/communication/alerts/{quote(alert_id, safe='')}/approve")
    if result:
        get_alerts.clear()
    return result


def dispatch_admin_alert_whatsapp(alert_id: str) -> dict[str, Any] | None:
    """Dispatch an approved alert via WhatsApp broadcast."""
    return _request_admin("POST", f"/communication/alerts/{quote(alert_id, safe='')}/dispatch/whatsapp")


def get_admin_alert_delivery(alert_id: str) -> dict[str, Any] | None:
    """Fetch WhatsApp delivery status counts for an alert."""
    return _request_admin("GET", f"/communication/alerts/{quote(alert_id, safe='')}/delivery")


def get_plan_action_history(plan_id: str, step_number: int | None = None) -> list[dict[str, Any]]:
    """Fetch plan action modification audit history."""
    params = {"step_number": step_number} if step_number is not None else None
    data = _get_api(f"/planification/plans/{quote(plan_id, safe='')}/history", params=params)
    return data if isinstance(data, list) else []


def get_nisr_imports() -> list[dict[str, Any]]:
    data = _request_admin("GET", "/admin/nisr/imports")
    return data if isinstance(data, list) else []


def upload_nisr_release(filename: str, content: bytes, source_release: str, season: str) -> dict[str, Any] | None:
    path = "/admin/nisr/imports"
    if not admin_session_authenticated():
        errors = dict(st.session_state.get("admin_api_errors", {}))
        errors[path] = "Unlock the administrator tools before importing NISR data."
        st.session_state["admin_api_errors"] = errors
        return None
    try:
        response = requests.post(
            f"{API_BASE_URL}{path}",
            files={"file": (filename, content, "text/csv")},
            data={"source_release": source_release, "season": season},
            headers=_admin_headers(),
            timeout=60,
        )
        response.raise_for_status()
        errors = dict(st.session_state.get("admin_api_errors", {}))
        errors.pop(path, None)
        st.session_state["admin_api_errors"] = errors
        return response.json()
    except requests.RequestException as exc:
        logger.error("Admin API POST %s failed: %s", path, exc)
        detail = None
        if exc.response is not None:
            try:
                body = exc.response.json()
                detail = body.get("detail") if isinstance(body, dict) else None
            except (ValueError, requests.RequestException):
                detail = None
        errors = dict(st.session_state.get("admin_api_errors", {}))
        errors[path] = str(detail or "Upload request failed. Check the backend connection and admin access.")
        st.session_state["admin_api_errors"] = errors
        return None


def get_health() -> dict[str, Any] | None:
    """GET /health: system health check."""
    data = _get_api("/health")
    return data if isinstance(data, dict) else None


def _request_admin(method: str, path: str, payload: dict[str, Any] | None = None, timeout: int = 15) -> Any:
    if not admin_session_authenticated():
        logger.info("Admin session required; skipping %s", path)
        errors = dict(st.session_state.get("admin_api_errors", {}))
        errors[path] = "Unlock the administrator tools to access this operation."
        st.session_state["admin_api_errors"] = errors
        return None
    try:
        response = requests.request(
            method,
            f"{API_BASE_URL}{path}",
            json=payload,
            headers=_admin_headers(),
            timeout=timeout,
        )
        response.raise_for_status()
        errors = dict(st.session_state.get("admin_api_errors", {}))
        errors.pop(path, None)
        st.session_state["admin_api_errors"] = errors
        return response.json()
    except requests.RequestException as exc:
        logger.error("Admin API %s %s failed: %s", method, path, exc)
        detail = None
        response = getattr(exc, "response", None)
        if response is not None:
            try:
                payload = response.json()
                detail = payload.get("detail") if isinstance(payload, dict) else None
            except (ValueError, requests.RequestException):
                detail = None
        errors = dict(st.session_state.get("admin_api_errors", {}))
        errors[path] = str(detail or f"Request failed with HTTP {response.status_code if response is not None else 'network error'}.")
        st.session_state["admin_api_errors"] = errors
        return None
