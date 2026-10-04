from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

_FIELD_REPORTS: list[dict[str, Any]] = []


def submit_field_report(
    zone_id: str,
    district: str,
    crop: str,
    rainfall_mm: float | None = None,
    soil_moisture_pct: float | None = None,
    symptoms: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    payload = {
        "zone_id": str(zone_id),
        "district": district,
        "crop": crop,
        "rainfall_mm": rainfall_mm,
        "soil_moisture_pct": soil_moisture_pct,
        "symptoms": symptoms or "",
        "notes": notes or "",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }
    _FIELD_REPORTS.insert(0, payload)
    return payload


def list_field_reports(zone_id: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
    records = _FIELD_REPORTS
    if zone_id:
        records = [item for item in records if item.get("zone_id") == str(zone_id)]
    return records[:limit]


def get_field_risk_summary(crop: str | None = None) -> dict[str, Any]:
    reports = _FIELD_REPORTS
    if crop:
        reports = [item for item in reports if str(item.get("crop", "")).lower() == str(crop).lower()]
    if not reports:
        return {"total_reports": 0, "risk_level": "Low", "notes": "No live field reports yet."}

    risk = "Low"
    for report in reports:
        symptoms = str(report.get("symptoms") or "").lower()
        if any(token in symptoms for token in ["yellow", "wilting", "brown", "lesion", "mold", "rust", "spot"]):
            risk = "Medium"
            break
        if any(token in symptoms for token in ["severe", "collapse", "fungus", "rapid spread", "burnt"]):
            risk = "High"
            break

    return {
        "total_reports": len(reports),
        "risk_level": risk,
        "latest_report": reports[0],
    }
