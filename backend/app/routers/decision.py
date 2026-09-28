from fastapi import APIRouter, HTTPException
from app.models.prediction import PredictionRequest, PredictionResult
from app.db import crud
from app.ml.predict import predict_yield, classify_priority
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
    priority = classify_priority(predicted_yield, request.area_cultivated)

    result = PredictionResult(
        zone_id=request.zone_id,
        season=request.season,
        crop=request.crop,
        predicted_yield=predicted_yield,
        priority_level=priority,
        confidence=confidence,
        model_version=model_version,
    )

    crud.save_prediction(result.model_dump(mode="json"))
    return result


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
