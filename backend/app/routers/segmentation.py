from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from app.core.auth import require_user
from app.models.zone import ZoneCreate
from app.db import crud

router = APIRouter(prefix="/segmentation", tags=["Segmentation"])


@router.get("/zones")
def get_zones(district: str | None = None):
    return crud.list_zones(district)


@router.post("/zones")
def add_zone(zone: ZoneCreate, _: dict = Depends(require_user)):
    return crud.create_zone(zone.model_dump())


@router.get("/map-data")
def get_map_data(district: str | None = None):
    """Zones joined with their latest prediction, ready for Folium."""
    zones = crud.list_zones(district)
    predictions = crud.list_predictions()
    latest_by_zone = {}
    for prediction in predictions:
        latest_by_zone.setdefault(str(prediction.get("zone_id")), prediction)
    enriched = []
    for zone in zones:
        latest = latest_by_zone.get(str(zone["id"]))
        enriched.append({
            **zone,
            "predicted_yield": latest.get("predicted_yield") if latest else None,
            "yield_per_ha": latest.get("yield_per_ha") if latest else None,
            "priority_level": latest.get("priority_level") if latest else None,
            "prediction_season": latest.get("season") if latest else None,
            "prediction_crop": latest.get("crop") if latest else None,
            "prediction_model_version": latest.get("model_version") if latest else None,
            "prediction_basis": (
                "baseline" if latest and "baseline" in str(latest.get("model_version", "")).casefold()
                else "model" if latest and latest.get("model_version") else None
            ),
        })
    return enriched


@router.get("/zones/{zone_id}")
def get_zone_detail(zone_id: UUID):
    zone = crud.get_zone(zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return zone


@router.get("/agri-metrics")
def browse_agri_metrics(district: str | None = None, crop: str | None = None,
                         season: str | None = None):
    """Browse the real SAS 2026 district x crop x season data directly -
    powers a filterable data table on the frontend (Dashboard / Segmentation
    pages) without needing a prediction first."""
    return crud.list_agri_metrics(season=season, crop=crop, district=district)


@router.get("/crop-comparison/{district}")
def crop_comparison(district: str, season: str | None = None):
    """All crops grown in a district, ranked by real yield - answers
    'what should this zone grow' directly from SAS data."""
    rows = crud.crop_comparison(district, season)
    if not rows:
        raise HTTPException(status_code=404, detail=f"No agri_metrics found for district '{district}'")
    return rows
