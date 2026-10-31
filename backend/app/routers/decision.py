from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
from app.core.auth import require_user
from app.models.prediction import PredictionRequest, PredictionResult
from app.db import crud
from app.db.rwanda_districts import RWANDA_DISTRICTS
from app.ml.predict import (
    classify_priority,
    known_crops,
    get_yield_gap,
    get_yield_index,
    predict_with_interval,
    model_provenance,
    get_model_info,
    get_district_evidence_ranking,
)
from app.ml.explain import explain_prediction
from app.services.disease_detector import detect_crop_disease
from app.services.recommendation_engine import get_recommendations

router = APIRouter(prefix="/decision", tags=["Decision Making"])


@router.post("/predict", response_model=PredictionResult)
def predict(request: PredictionRequest, _: dict = Depends(require_user)):
    zone = crud.get_zone(request.zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    district = str(zone.get("district") or "").strip()
    district_by_name = {item["district"].casefold(): item["district"] for item in RWANDA_DISTRICTS}
    if district.casefold() not in district_by_name:
        raise HTTPException(status_code=422, detail="Yield decisions are currently supported for Rwanda's 30 districts only")
    district = district_by_name[district.casefold()]

    interval = predict_with_interval(district, request.crop, request.season,
                                     allow_category_proxy=request.allow_category_proxy,
                                     crop_category=request.crop_category)
    explanation = explain_prediction(district, request.crop, request.season)
    provenance = model_provenance()

    # analysis fields (not persisted beyond the prediction record)
    gap = get_yield_gap(district, request.crop, request.season)
    yi = get_yield_index(district, request.crop, request.season)
    area = request.area_cultivated if request.area_cultivated and request.area_cultivated > 0 else None
    # Rainfall is not a validated prediction feature; it does not scale yield.
    predicted_yield_per_ha = interval["point"]
    predicted_yield = (round(predicted_yield_per_ha * area, 1)
                       if predicted_yield_per_ha is not None and area is not None else None)
    model_version = interval.get("model_version") or interval.get("basis") or "no-yield-data"
    benchmark_yield_per_ha = gap.get("benchmark_yield_per_ha")
    yield_gap_kg_ha = (
        round(max(0.0, benchmark_yield_per_ha - predicted_yield_per_ha), 1)
        if benchmark_yield_per_ha is not None and predicted_yield_per_ha is not None
        else None
    )

    priority_yield = predicted_yield if predicted_yield is not None else predicted_yield_per_ha
    priority = (classify_priority(priority_yield, request.area_cultivated,
                                  district, request.crop, request.season)
                if priority_yield is not None else {
                    "priority_level": "Unknown", "underlying_priority_level": "Unknown",
                    "priority_status": "no_yield_data", "reasons": ["No yield observations for this crop."],
                    "components": {"district_observations": interval["district_observations"]},
                    "low_evidence": True, "fold_priorities": [], "priority_changes_across_folds": 0})

    result = PredictionResult(
        zone_id=request.zone_id,
        season=request.season,
        crop=request.crop,
        predicted_yield=predicted_yield,
        priority_level=priority["priority_level"],
        # Interval width is uncertainty information, not a calibrated probability.
        confidence=None,
        confidence_basis=None,
        model_version=model_version,
        evidence_source=interval.get("evidence_source"),
        evidence_period=interval.get("evidence_period"),
        evidence_scope=interval.get("evidence_scope"),
        model_trained_on=provenance["model_trained_on"],
        basis=(interval["basis"] if interval["basis"] == "category_proxy" else
               "model" if interval["basis"] == "model" else "baseline"),
        yield_data_status=("no_data" if interval["point"] is None else
                           "category_proxy" if interval["basis"] == "category_proxy" else "available"),
        district_observations=interval["district_observations"],
        thin=interval["thin"], warning=(interval.get("warning") or
              ("Total output and total-output intervals require a supplied cultivated area in hectares."
               if interval["point"] is not None and area is None else None)),
        predicted_yield_low=(round(interval["low"] * area, 1) if area is not None and interval["low"] is not None else None),
        predicted_yield_high=(round(interval["high"] * area, 1) if area is not None and interval["high"] is not None else None),
        interval_level=interval["interval_level"],
        explanation_factors=explanation["factors"],
        expected_yield_given_inputs_kg_ha=explanation["expected_yield_given_inputs_kg_ha"],
        actual_yield_kg_ha=explanation["actual_yield_kg_ha"],
        explanation_diagnosis=explanation["diagnosis"],
        interpretation_note=explanation["interpretation_note"],
        priority_status=priority["priority_status"],
        priority_reasons=priority["reasons"],
        priority_components=priority["components"],
        priority_low_evidence=priority["low_evidence"],
        priority_fold_labels=priority["fold_priorities"],
        priority_changes_across_folds=priority["priority_changes_across_folds"],
        yield_per_ha=predicted_yield_per_ha,
        benchmark_yield_per_ha=benchmark_yield_per_ha,
        yield_gap_kg_ha=yield_gap_kg_ha,
        yield_index=yi,
    )

    persistence_payload = result.model_dump(mode="json")
    persistence_payload["priority_level"] = priority["underlying_priority_level"]
    crud.save_prediction(persistence_payload)
    return result


@router.get("/crops")
def list_crops():
    return known_crops()


@router.get("/model-info")
def model_info():
    return get_model_info()


@router.get("/district-ranking")
def district_ranking(crop: str, season: str | None = None):
    if crop not in known_crops():
        raise HTTPException(status_code=404, detail="Unknown crop")
    evidence = get_district_evidence_ranking(crop, season)
    reference = evidence.get("national_reference_kg_ha")
    result = []
    for item in evidence["rows"]:
        value = item["yield_kg_ha"]
        result.append({
            "district": item["district"], "yield_per_ha": value,
            "benchmark_yield_per_ha": reference,
            "yield_gap_kg_ha": round(max(0.0, reference - value), 1) if reference is not None else None,
            "yield_index": round(value / reference, 4) if reference else None,
            "observation_count": item["observation_count"], "seasons": item["seasons"],
            "sources": item["sources"], "rank": item["rank"],
            "cultivated_area_ha": None, "potential_gain_mt": None,
        })
    return result


@router.get("/evidence-ranking")
def evidence_ranking(crop: str, season: str | None = None):
    """Compare only districts with crop observations; missing districts stay absent."""
    if crop not in known_crops():
        raise HTTPException(status_code=404, detail="Unknown crop")
    try:
        return get_district_evidence_ranking(crop, season)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Yield evidence is temporarily unavailable") from exc


@router.get("/priority-ranking")
def get_priority_ranking(
    season: str | None = None,
    include_recommendations: bool = False,
    limit: int = Query(default=20, ge=1, le=100),
):
    """Return saved assessments in one request; optionally attach actionable context.

    Recommendations are derived from the stored assessment and explanatory
    factors. They remain suggestions for review, not field instructions.
    """
    rows = crud.priority_ranking(season)[:limit]
    if not include_recommendations:
        return rows
    for row in rows:
        zone_id = row.get("zone_id")
        zone = row.get("zones") or {}
        explanation = explain_prediction(
            zone.get("district"), row.get("crop", ""), row.get("season")
        )
        row["recommendations"] = get_recommendations(
            row.get("priority_level", "Unknown"), None, None, explanation["factors"]
        )
        row["explanation_factors"] = explanation["factors"]
        row["explanation_diagnosis"] = explanation["diagnosis"]
        row["interpretation_note"] = explanation["interpretation_note"]
    return rows


@router.get("/recommendations/{zone_id}")
def recommendations(zone_id: UUID, rainfall_mm: float | None = None, soil_type: str | None = None,
                    _: dict = Depends(require_user)):
    predictions = crud.list_predictions(zone_id)
    if not predictions:
        raise HTTPException(status_code=404, detail="No predictions found for this zone yet")

    latest = predictions[0]
    zone = crud.get_zone(zone_id)
    explanation = explain_prediction(zone.get("district") if zone else None,
                                     latest.get("crop", ""), latest.get("season"))
    return {
        "zone_id": zone_id,
        "crop": latest.get("crop"),
        "season": latest.get("season"),
        "priority_level": latest["priority_level"],
        "model_version": latest.get("model_version"),
        "recommendations": get_recommendations(latest["priority_level"], rainfall_mm, soil_type,
                                               explanation["factors"]),
        "explanation_factors": explanation["factors"],
        "explanation_diagnosis": explanation["diagnosis"],
        "interpretation_note": explanation["interpretation_note"],
    }


@router.post("/disease-risk")
def disease_risk(zone_id: UUID, crop: str, symptoms: str, image_description: str | None = None,
                 _: dict = Depends(require_user)):
    zone = crud.get_zone(zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    assessment = detect_crop_disease(crop, symptoms, image_description)
    return {
        "zone_id": zone_id,
        "crop": assessment["crop"],
        "predicted_disease": assessment["predicted_disease"],
        "plant_identification": assessment.get("plant_identification", "Not confirmed"),
        "confidence": assessment["confidence"],
        "risk_level": assessment["risk_level"],
        "urgency": assessment.get("urgency", "unclear"),
        "observations": assessment.get("observations", []),
        "possible_causes": assessment.get("possible_causes", []),
        "recommended_actions": assessment["recommended_actions"],
        "source": assessment.get("source", "unavailable"),
        "interpretation_note": assessment.get("interpretation_note"),
    }
