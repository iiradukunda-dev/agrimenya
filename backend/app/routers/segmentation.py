from fastapi import APIRouter, HTTPException

from app.db import crud
from app.models.zone import ZoneCreate

router = APIRouter(prefix="/segmentation", tags=["Segmentation"])


@router.get("/zones")
def get_zones(district: str | None = None):
    return crud.list_zones(district)


@router.post("/zones")
def add_zone(zone: ZoneCreate):
    return crud.create_zone(zone.model_dump())


@router.get("/map-data")
def get_map_data(district: str | None = None):
    """Zones joined with their latest prediction, ready for Folium."""
    zones = crud.list_zones(district)
    enriched = []
    for zone in zones:
        predictions = crud.list_predictions(zone["id"])
        latest = predictions[0] if predictions else None
        enriched.append({
            **zone,
            "predicted_yield": latest["predicted_yield"] if latest else None,
            "priority_level": latest["priority_level"] if latest else None,
        })
    return enriched


@router.get("/zones/{zone_id}")
def get_zone_detail(zone_id: str):
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
