from __future__ import annotations

from typing import Any

import httpx

DISTRICT_COORDS = {
    "gasabo": (-1.9441, 30.0619),
    "kigali city": (-1.9441, 30.0619),
    "rubavu": (-1.695, 29.247),
    "muhanga": (-2.085, 29.757),
    "karongi": (-1.964, 29.298),
    "nyagatare": (-1.298, 30.321),
    "huye": (-2.596, 29.739),
    "rwamagana": (-1.946, 30.434),
    "rusizi": (-2.485, 28.912),
    "nyarugenge": (-1.95, 30.05),
}


def _fallback_weather(district: str | None) -> dict[str, Any]:
    normalized = (district or "kigali city").strip().lower()
    lat, lon = DISTRICT_COORDS.get(normalized, DISTRICT_COORDS["kigali city"])
    return {
        "district": district or "Kigali City",
        "source": "fallback",
        "latitude": lat,
        "longitude": lon,
        "temperature_c": 24.5,
        "rainfall_mm": 38.0,
        "humidity_pct": 68,
        "wind_kph": 12.0,
        "summary": "Fallback weather snapshot used while the live provider is unavailable.",
        "updated_at": "offline",
    }


def fetch_weather(district: str | None = None, latitude: float | None = None, longitude: float | None = None) -> dict[str, Any]:
    normalized = (district or "kigali city").strip().lower()
    lat = latitude
    lon = longitude
    if lat is None or lon is None:
        lat, lon = DISTRICT_COORDS.get(normalized, DISTRICT_COORDS["kigali city"])

    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,precipitation,rain,wind_speed_10m",
            "timezone": "auto",
        }
        response = httpx.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=10.0)
        response.raise_for_status()
        payload = response.json()
        current = payload.get("current", {})
        summary = {
            "district": district or "Kigali City",
            "source": "open-meteo",
            "latitude": lat,
            "longitude": lon,
            "temperature_c": current.get("temperature_2m"),
            "rainfall_mm": current.get("precipitation") or current.get("rain") or 0.0,
            "humidity_pct": current.get("relative_humidity_2m"),
            "wind_kph": current.get("wind_speed_10m"),
            "summary": "Live weather snapshot from Open-Meteo.",
            "updated_at": current.get("time"),
        }
        return summary
    except Exception:
        return _fallback_weather(district)
