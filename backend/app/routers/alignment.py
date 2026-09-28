from fastapi import APIRouter, HTTPException
from app.db import crud
from app.services.alignment_calculator import calculate_alignment_metrics

router = APIRouter(prefix="/alignment", tags=["National Alignment"])


@router.post("/compute/{zone_id}")
def compute_alignment(zone_id: str, season: str, predicted_yield: float,
                       area_cultivated: float | None = None, rainfall_mm: float | None = None,
                       priority_level: str = "Medium"):
    zone = crud.get_zone(zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    metrics = calculate_alignment_metrics(predicted_yield, area_cultivated, rainfall_mm, priority_level)
    record = {"zone_id": zone_id, "season": season, **metrics}
    return crud.upsert_alignment_metric(record)


@router.get("/finance-readiness/{zone_id}")
def finance_readiness(zone_id: str):
    metric = crud.get_alignment_metric(zone_id)
    if not metric:
        raise HTTPException(status_code=404, detail="No alignment data for this zone yet")
    return {
        "zone_id": zone_id,
        "credit_insurance_score": metric["credit_insurance_score"],
    }


@router.get("/nutrition-risk/{zone_id}")
def nutrition_risk(zone_id: str):
    metric = crud.get_alignment_metric(zone_id)
    if not metric:
        raise HTTPException(status_code=404, detail="No alignment data for this zone yet")
    return {
        "zone_id": zone_id,
        "nutrition_risk_level": metric["nutrition_risk_level"],
    }


@router.get("/export-flags")
def export_flags():
    metrics = crud.list_alignment_metrics()
    return [m for m in metrics if m.get("export_readiness_flag")]


@router.get("/dashboard")
def national_dashboard():
    metrics = crud.list_alignment_metrics()
    if not metrics:
        return {"message": "No alignment data yet - run /alignment/compute for your zones first."}

    total = len(metrics)
    avg_irrigation = sum(m.get("irrigation_ha", 0) for m in metrics) / total
    avg_terraces = sum(m.get("terraces_ha", 0) for m in metrics) / total
    scores = [m.get("credit_insurance_score") for m in metrics if m.get("credit_insurance_score") is not None]
    avg_credit_score = sum(scores) / len(scores) if scores else 0

    return {
        "total_zones": total,
        "avg_irrigation_ha": round(avg_irrigation, 2),
        "avg_terraces_ha": round(avg_terraces, 2),
        "avg_credit_insurance_score": round(avg_credit_score, 1),
        "zones_high_nutrition_risk": sum(1 for m in metrics if m.get("nutrition_risk_level") == "High"),
        "zones_high_climate_risk": sum(1 for m in metrics if m.get("climate_risk_level") == "High"),
        "zones_export_ready": sum(1 for m in metrics if m.get("export_readiness_flag")),
        "total_estimated_jobs": sum(m.get("estimated_jobs_supported", 0) for m in metrics),
    }
