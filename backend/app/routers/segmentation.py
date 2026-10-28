from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
from app.core.auth import require_community_or_admin
from app.models.zone import ZoneCreate
from app.db import crud
from app.db.rwanda_districts import RWANDA_DISTRICTS

router = APIRouter(prefix="/segmentation", tags=["Segmentation"])


@router.get("/districts")
def list_districts():
    """Return the canonical Rwanda district list for coverage and zone entry."""
    return RWANDA_DISTRICTS


@router.get("/zones")
def get_zones(district: str | None = None):
    return crud.list_zones(district)


@router.get("/zones/summary")
def get_zone_registry_summary():
    return crud.zone_registry_summary()


@router.get("/zones/page")
def get_zones_page(
    zone_id: UUID | None = None, district: str | None = None, crop: str | None = None, season: str | None = None,
    search: str | None = None, limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """Search zones without loading the whole registry into the client."""
    result = crud.list_zones_page(
        zone_id=str(zone_id) if zone_id else None,
        district=district, crop=crop, season=season, search=search, limit=limit, offset=offset,
    )
    zone_ids = [str(item.get("id")) for item in result["items"] if item.get("id")]
    predictions = crud.list_predictions(zone_ids=zone_ids) if zone_ids else []
    latest_by_zone = {}
    for prediction in predictions:
        latest_by_zone.setdefault(str(prediction.get("zone_id")), prediction)
    for zone in result["items"]:
        latest = latest_by_zone.get(str(zone.get("id")))
        zone.update({
            "predicted_yield": latest.get("predicted_yield") if latest else None,
            "priority_level": latest.get("priority_level") if latest else None,
            "prediction_season": latest.get("season") if latest else None,
            "prediction_crop": latest.get("crop") if latest else None,
            "prediction_model_version": latest.get("model_version") if latest else None,
        })
    return result


@router.post("/zones")
def add_zone(zone: ZoneCreate, _: dict = Depends(require_community_or_admin)):
    canonical_district = next(
        (item["district"] for item in RWANDA_DISTRICTS
         if item["district"].casefold() == zone.district.strip().casefold()),
        None,
    )
    if not canonical_district:
        raise HTTPException(status_code=422, detail="Choose one of Rwanda's 30 districts")
    payload = zone.model_dump()
    payload["district"] = canonical_district
    return crud.create_zone(payload)


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
            "prediction_basis": latest.get("basis") if latest else None,
            "prediction_evidence_source": latest.get("evidence_source") if latest else None,
            "prediction_evidence_period": latest.get("evidence_period") if latest else None,
            "prediction_evidence_scope": latest.get("evidence_scope") if latest else None,
            "prediction_yield_data_status": latest.get("yield_data_status") if latest else None,
            "prediction_confidence": latest.get("confidence") if latest else None,
            "prediction_interval_low": latest.get("predicted_yield_low") if latest else None,
            "prediction_interval_high": latest.get("predicted_yield_high") if latest else None,
            "prediction_warning": latest.get("warning") if latest else None,
            "prediction_priority_reasons": latest.get("priority_reasons") if latest else [],
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


@router.get("/agri-metrics/page")
def browse_agri_metrics_page(
    district: str | None = None, crop: str | None = None, season: str | None = None,
    search: str | None = None, limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """Page through persisted yield observations using server-side filters."""
    return crud.list_agri_metrics_page(
        district=district, crop=crop, season=season, search=search, limit=limit, offset=offset,
    )


@router.get("/crop-comparison/{district}")
def crop_comparison(district: str, season: str | None = None):
    """All crops grown in a district, ranked by real yield - answers
    'what should this zone grow' directly from SAS data."""
    rows = crud.crop_comparison(district, season)
    if not rows:
        raise HTTPException(status_code=404, detail=f"No agri_metrics found for district '{district}'")
    return rows
