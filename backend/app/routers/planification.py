from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
import math
from app.core.auth import require_user
from app.models.plan import PlanCreate
from app.db import crud
from app.services.disease_detector import detect_crop_disease
from app.services.resource_estimator import estimate_resources

router = APIRouter(prefix="/planification", tags=["Planification"])


@router.get("/resources/{zone_id}")
def get_resource_estimate(zone_id: UUID, area_cultivated: float | None = None,
                           rainfall_mm: float | None = None,
                           seed_rate_kg_ha: float | None = None, seed_price_rwf_kg: float | None = None,
                           dap_rate_kg_ha: float | None = None, dap_price_rwf_kg: float | None = None,
                           urea_rate_kg_ha: float | None = None, urea_price_rwf_kg: float | None = None,
                           irrigation_liters_ha: float | None = None,
                           irrigation_price_rwf_1000_liters: float | None = None,
                           _: dict = Depends(require_user)):
    if not crud.get_zone(zone_id):
        raise HTTPException(status_code=404, detail="Zone not found")
    inputs = {
        "seed_rate_kg_ha": seed_rate_kg_ha, "seed_price_rwf_kg": seed_price_rwf_kg,
        "dap_rate_kg_ha": dap_rate_kg_ha, "dap_price_rwf_kg": dap_price_rwf_kg,
        "urea_rate_kg_ha": urea_rate_kg_ha, "urea_price_rwf_kg": urea_price_rwf_kg,
        "irrigation_liters_ha": irrigation_liters_ha,
        "irrigation_price_rwf_1000_liters": irrigation_price_rwf_1000_liters,
    }
    supplied_values = [area_cultivated, rainfall_mm, *inputs.values()]
    if any(value is not None and (not math.isfinite(value) or value < 0) for value in supplied_values):
        raise HTTPException(status_code=422, detail="Resource rates and prices must be non-negative")
    result = estimate_resources(area_cultivated, rainfall_mm, **inputs)
    quantities = result["quantities"]
    if "dap_kg" in quantities or "urea_kg" in quantities:
        result["fertilizer_kg"] = quantities.get("fertilizer_kg")
    result.update({"seeds_kg": quantities.get("seeds_kg"),
                   "dap_kg": quantities.get("dap_kg"), "urea_kg": quantities.get("urea_kg"),
                   "irrigation_liters": quantities.get("irrigation_liters")})
    return result


@router.post("/roadmap")
def create_roadmap(plan: PlanCreate, _: dict = Depends(require_user)):
    zone = crud.get_zone(plan.zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    record = {
        "zone_id": str(plan.zone_id),
        "title": plan.title,
        "roadmap_json": [step.model_dump() for step in plan.roadmap],
        "resources_json": plan.resources.model_dump(),
        "created_by": plan.created_by,
    }
    return crud.create_plan(record)


@router.get("/plans/{zone_id}")
def get_plans(zone_id: UUID, _: dict = Depends(require_user)):
    return crud.list_plans(zone_id)


@router.post("/disease-plan")
def create_disease_plan(zone_id: UUID, crop: str, symptoms: str, image_description: str | None = None,
                        _: dict = Depends(require_user)):
    zone = crud.get_zone(zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    assessment = detect_crop_disease(crop, symptoms, image_description)
    return {
        "zone_id": zone_id,
        "crop": assessment["crop"],
        "predicted_disease": assessment["predicted_disease"],
        "risk_level": assessment["risk_level"],
        "recommended_actions": assessment["recommended_actions"],
        "interpretation_note": assessment.get("interpretation_note"),
        "roadmap": [
            "Record symptoms and request an in-person assessment from an RAB or district agronomist.",
            "Confirm the cause with a qualified agronomist before applying any treatment.",
            "Follow the relevant authority's instructions for any follow-up visit or treatment.",
        ],
    }
