from fastapi import APIRouter, HTTPException

from app.db import crud
from app.ml.predict import (
    classify_priority,
    get_yield_gap,
    get_yield_index,
    known_crops,
    predict_yield,
)
from app.models.prediction import PredictionRequest, PredictionResult
from app.services.recommendation_engine import get_recommendations

router = APIRouter(prefix="/decision", tags=["Decision Making"])


@router.post("/predict", response_model=PredictionResult)
def predict(request: PredictionRequest):
    zone = crud.get_zone(request.zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    predicted_yield, confidence, model_version = predict_yield(
        zone.get("district"), request.crop, request.season,
        request.rainfall_mm, request.area_cultivated, request.household_size,
    )

    # analysis fields (not persisted beyond the prediction record)
    gap = get_yield_gap(zone.get("district"), request.crop)
    yi = get_yield_index(zone.get("district"), request.crop)

    priority = classify_priority(predicted_yield, request.area_cultivated, zone.get("district"), request.crop)

    result = PredictionResult(
        zone_id=request.zone_id,
        season=request.season,
        crop=request.crop,
        predicted_yield=predicted_yield,
        priority_level=priority,
        confidence=confidence,
        model_version=model_version,
        yield_per_ha=gap.get("yield_per_ha"),
        benchmark_yield_per_ha=gap.get("benchmark_yield_per_ha"),
        yield_gap_kg_ha=gap.get("yield_gap_kg_ha"),
        yield_index=yi,
    )

    crud.save_prediction(result.model_dump(mode="json"))
    return result


@router.get("/crops")
def list_crops():
    return known_crops()


@router.get("/district-ranking")
def district_ranking(crop: str, season: str | None = None):
    # return all districts with analysis fields; 404 if unknown crop
    from app.db.rwanda_districts import RWANDA_DISTRICTS

    if crop not in known_crops():
        raise HTTPException(status_code=404, detail="Unknown crop")

    districts = [d["district"] for d in RWANDA_DISTRICTS]
    rows = []
    for d in districts:
        gap = get_yield_gap(d, crop)
        yp = gap.get("yield_per_ha")
        by = gap.get("benchmark_yield_per_ha")
        yg = gap.get("yield_gap_kg_ha")
        yi = get_yield_index(d, crop)
        # estimate cultivated area from agri_metrics if possible
        metrics = crud.list_agri_metrics(district=d, season=season, crop=crop)
        cultivated = None
        if metrics:
            cultivated = sum((m.get("area_cultivated") or 0) for m in metrics)

        rows.append({
            "district": d,
            "yield_per_ha": yp,
            "benchmark_yield_per_ha": by,
            "yield_gap_kg_ha": yg,
            "yield_index": yi,
            "cultivated_area_ha": cultivated,
            # potential_gain_mt = yield_gap_kg_ha * cultivated_area / 1000
            "potential_gain_mt": round(((yg or 0.0) * (cultivated or 0)) / 1000.0, 3) if cultivated else None,
        })

    # sort worst-priority-first: highest gap or lowest yield_index
    def sort_key(r):
        if r["yield_index"] is None:
            return float("inf")
        return r["yield_index"]

    rows_sorted = sorted(rows, key=sort_key)
    return rows_sorted


@router.get("/priority-ranking")
def get_priority_ranking(season: str | None = None):
    return crud.priority_ranking(season)


@router.get("/recommendations/{zone_id}")
def recommendations(zone_id: str, rainfall_mm: float | None = None, soil_type: str | None = None):
    predictions = crud.list_predictions(zone_id)
    if not predictions:
        raise HTTPException(status_code=404, detail="No predictions found for this zone yet")

    latest = predictions[0]
    return {
        "zone_id": zone_id,
        "priority_level": latest["priority_level"],
        "recommendations": get_recommendations(latest["priority_level"], rainfall_mm, soil_type),
    }
