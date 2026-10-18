from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from app.core.auth import require_user
from app.models.prediction import PredictionRequest, PredictionResult
from app.db import crud
from app.db.rwanda_districts import RWANDA_DISTRICTS
from app.ml.predict import (
    predict_yield,
    classify_priority,
    known_crops,
    get_yield_gap,
    get_yield_index,
    predict_with_interval,
    model_provenance,
    get_model_info,
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

    predicted_yield, confidence, model_version = predict_yield(
        district, request.crop, request.season,
        request.rainfall_mm, request.area_cultivated, request.household_size,
        request.allow_category_proxy, request.crop_category,
    )
    interval = predict_with_interval(district, request.crop, request.season,
                                     allow_category_proxy=request.allow_category_proxy,
                                     crop_category=request.crop_category)
    explanation = explain_prediction(district, request.crop, request.season)
    confidence_basis = interval["basis"]
    provenance = model_provenance()

    # analysis fields (not persisted beyond the prediction record)
    gap = get_yield_gap(district, request.crop, request.season)
    yi = get_yield_index(district, request.crop, request.season)
    area = request.area_cultivated if request.area_cultivated and request.area_cultivated > 0 else None
    # Rainfall is not a validated prediction feature; it does not scale yield.
    predicted_yield_per_ha = interval["point"]
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
        confidence=(min(1.0, max(0.0, 1.0 / (1.0 +
                    (interval["high"] - interval["low"]) / max(2.0 * interval["point"], 1e-9))))
                    if interval["point"] is not None and interval["low"] is not None and interval["high"] is not None
                    else confidence),
        confidence_basis=confidence_basis,
        model_version=model_version,
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
    # return all districts with analysis fields; 404 if unknown crop
    from app.db.rwanda_districts import RWANDA_DISTRICTS

    if crop not in known_crops():
        raise HTTPException(status_code=404, detail="Unknown crop")

    source_metrics = crud.list_agri_metrics(season=season, crop=crop)
    metrics_by_district = {}
    for metric in source_metrics:
        district_name = (metric.get("zones") or {}).get("district")
        if district_name:
            metrics_by_district.setdefault(district_name.casefold(), []).append(metric)

    districts = [d["district"] for d in RWANDA_DISTRICTS]
    rows = []
    for d in districts:
        gap = get_yield_gap(d, crop, season)
        yp = gap.get("yield_per_ha")
        by = gap.get("benchmark_yield_per_ha")
        yg = gap.get("yield_gap_kg_ha")
        yi = get_yield_index(d, crop, season)
        # estimate cultivated area from agri_metrics if possible
        metrics = metrics_by_district.get(d.casefold(), [])
        cultivated = None
        if metrics:
            by_season = {}
            for metric in metrics:
                season_key = str(metric.get("season", "")).casefold()
                by_season.setdefault(season_key, {})[str(metric.get("zone_id"))] = float(metric.get("area_cultivated") or 0)
            seasonal_totals = [sum(zone_areas.values()) for zone_areas in by_season.values()]
            # When no season is selected, use the largest single season's
            # exposure to avoid counting the same cultivated land twice.
            cultivated = sum(next(iter(by_season.values())).values()) if season and by_season else (
                max(seasonal_totals) if seasonal_totals else None)

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
        "priority_level": latest["priority_level"],
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
        "confidence": assessment["confidence"],
        "risk_level": assessment["risk_level"],
        "recommended_actions": assessment["recommended_actions"],
        "interpretation_note": assessment.get("interpretation_note"),
    }
