from __future__ import annotations

from typing import Any

from app.db import crud


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
    }
    return crud.create_field_report(payload)


def list_field_reports(zone_id: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
    if not zone_id:
        return []
    return crud.list_field_reports(zone_id, limit)


def get_field_risk_summary(crop: str | None = None, zone_id: str | None = None) -> dict[str, Any]:
    reports = list_field_reports(zone_id=zone_id, limit=100) if zone_id else []
    if crop:
        reports = [item for item in reports if str(item.get("crop", "")).lower() == str(crop).lower()]
    if not reports:
        return {"total_reports": 0, "risk_level": "Low", "notes": "No live field reports yet."}

    risk = "Low"
    for report in reports:
        symptoms = str(report.get("symptoms") or "").lower()
        if any(token in symptoms for token in ["severe", "collapse", "fungus", "rapid spread", "burnt"]):
            risk = "High"
            break
        if any(token in symptoms for token in ["yellow", "wilting", "brown", "lesion", "mold", "rust", "spot"]):
            risk = "Medium"
            break

    return {
        "total_reports": len(reports),
        "risk_level": risk,
        "latest_report": reports[0],
    }
