from __future__ import annotations

import logging
from typing import Any

import httpx
from app.db.rwanda_districts import DISTRICT_LOOKUP

logger = logging.getLogger(__name__)

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

# Supply a district centroid for every district so local weather requests
# never silently use Kigali coordinates for another part of the country.
for _district_name, _district in DISTRICT_LOOKUP.items():
    DISTRICT_COORDS.setdefault(
        _district_name.lower(),
        (_district["latitude"], _district["longitude"]),
    )


def _fallback_weather(district: str | None) -> dict[str, Any]:
    return {
        "district": district,
        "source": "unavailable",
        "latitude": None,
        "longitude": None,
        "temperature_c": None,
        "rainfall_mm": None,
        "humidity_pct": None,
        "wind_kph": None,
        "summary": "Weather data is unavailable; no fallback values are substituted.",
        "updated_at": None,
        "forecast": [],
    }


def fetch_weather(district: str | None = None, latitude: float | None = None, longitude: float | None = None) -> dict[str, Any]:
    normalized = (district or "kigali city").strip().lower()
    lat = latitude
    lon = longitude
    if lat is None or lon is None:
        coordinates = DISTRICT_COORDS.get(normalized)
        if coordinates is None:
            return _fallback_weather(district)
        lat, lon = coordinates

    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,precipitation,rain,wind_speed_10m",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum",
            "forecast_days": 5,
            "timezone": "auto",
        }
        response = httpx.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=10.0)
        response.raise_for_status()
        payload = response.json()
        current = payload.get("current", {})
        daily = payload.get("daily", {})
        forecast = [
            {
                "date": date,
                "temperature_max_c": daily.get("temperature_2m_max", [])[index],
                "temperature_min_c": daily.get("temperature_2m_min", [])[index],
                "precipitation_probability_pct": daily.get("precipitation_probability_max", [])[index],
                "precipitation_sum_mm": daily.get("precipitation_sum", [])[index],
            }
            for index, date in enumerate(daily.get("time", []))
            if all(index < len(daily.get(key, [])) for key in (
                "temperature_2m_max", "temperature_2m_min",
                "precipitation_probability_max", "precipitation_sum",
            ))
        ]
        summary = {
            "district": district or "Kigali City",
            "source": "open-meteo",
            "latitude": lat,
            "longitude": lon,
            "temperature_c": current.get("temperature_2m"),
            "rainfall_mm": current.get("precipitation") if current.get("precipitation") is not None else current.get("rain"),
            "humidity_pct": current.get("relative_humidity_2m"),
            "wind_kph": current.get("wind_speed_10m"),
            "summary": "Live weather snapshot from Open-Meteo.",
            "updated_at": current.get("time"),
            "forecast": forecast,
        }
        return summary
    except Exception:
        logger.exception("Live weather request failed for district %s", district)
        return _fallback_weather(district)
