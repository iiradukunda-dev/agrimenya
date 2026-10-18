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
    field_risk = get_field_risk_summary(crop=crop, zone_id=zone_id)
    manual_observations = None
    if rainfall_mm is not None:
        manual_observations = {"rainfall_mm": rainfall_mm, "basis": "user-provided"}

    freshness = data_freshness_score(weather.get("updated_at"), max_age_hours=24)

    return {
        "zone_id": zone_id,
        "district": district or weather.get("district"),
        "crop": crop,
        "weather": weather,
        "manual_observations": manual_observations,
        "user_notes": notes,
        "field_reports": reports,
        "field_risk_summary": field_risk,
        "freshness": freshness,
        "source": "hybrid-live-baseline",
        "recommendation_bias": "use-live-observations-first",
    }
