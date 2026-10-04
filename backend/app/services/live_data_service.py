from __future__ import annotations

from typing import Any

from app.services.field_report_service import get_field_risk_summary, list_field_reports
from app.services.freshness_service import data_freshness_score
from app.services.weather_service import fetch_weather


def build_live_context(
    zone_id: str | None = None,
    district: str | None = None,
    crop: str | None = None,
    rainfall_mm: float | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    weather = fetch_weather(district=district)
    reports = list_field_reports(zone_id=zone_id, limit=5)
    field_risk = get_field_risk_summary(crop=crop)
    freshness = data_freshness_score(weather.get("updated_at"), max_age_hours=24)

    if rainfall_mm is not None:
        weather["rainfall_mm"] = rainfall_mm
        weather["source"] = "manual-input"

    if notes:
        weather["summary"] = notes

    return {
        "zone_id": zone_id,
        "district": district or weather.get("district"),
        "crop": crop,
        "weather": weather,
        "field_reports": reports,
        "field_risk_summary": field_risk,
        "freshness": freshness,
        "source": "hybrid-live-baseline",
        "recommendation_bias": "use-live-observations-first",
    }
