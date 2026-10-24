from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import date
from uuid import UUID
import math
from pydantic import BaseModel, Field
from app.core.auth import require_user
from app.models.plan import PlanCreate
from app.db import crud
from app.services.disease_detector import detect_crop_disease
from app.services.resource_estimator import estimate_resources

router = APIRouter(prefix="/planification", tags=["Planification"])


class PlanActionStatusUpdate(BaseModel):
    status: str = Field(pattern="^(planned|in_progress|completed|blocked)$")
    change_note: str = Field(default="", max_length=1000)


@router.get("/resources/{zone_id}")
def get_resource_estimate(zone_id: UUID, area_cultivated: float | None = None,
                           rainfall_mm: float | None = None,
                           seed_rate_kg_ha: float | None = None, seed_price_rwf_kg: float | None = None,
                           dap_rate_kg_ha: float | None = None, dap_price_rwf_kg: float | None = None,
                           urea_rate_kg_ha: float | None = None, urea_price_rwf_kg: float | None = None,
                           irrigation_liters_ha: float | None = None,
                           irrigation_price_rwf_1000_liters: float | None = None,
                           labor_days_ha: float | None = None, labor_price_rwf_day: float | None = None,
                           land_preparation_cost_rwf_ha: float | None = None,
                           crop_protection_cost_rwf_ha: float | None = None,
                           equipment_hire_cost_rwf_ha: float | None = None,
                           transport_cost_rwf_ha: float | None = None,
                           postharvest_cost_rwf_ha: float | None = None,
                           storage_packaging_cost_rwf_ha: float | None = None,
                           other_cost_rwf_ha: float | None = None,
                           contingency_pct: float | None = None,
                           area_source: str | None = Query(default=None, max_length=40),
                           rate_source: str | None = Query(default=None, max_length=200),
                           price_source: str | None = Query(default=None, max_length=200),
                           prices_checked_on: date | None = None,
                           _: dict = Depends(require_user)):
    if not crud.get_zone(zone_id):
        raise HTTPException(status_code=404, detail="Zone not found")
    inputs = {
        "seed_rate_kg_ha": seed_rate_kg_ha, "seed_price_rwf_kg": seed_price_rwf_kg,
        "dap_rate_kg_ha": dap_rate_kg_ha, "dap_price_rwf_kg": dap_price_rwf_kg,
        "urea_rate_kg_ha": urea_rate_kg_ha, "urea_price_rwf_kg": urea_price_rwf_kg,
        "irrigation_liters_ha": irrigation_liters_ha,
        "irrigation_price_rwf_1000_liters": irrigation_price_rwf_1000_liters,
        "labor_days_ha": labor_days_ha, "labor_price_rwf_day": labor_price_rwf_day,
        "land_preparation_cost_rwf_ha": land_preparation_cost_rwf_ha,
        "crop_protection_cost_rwf_ha": crop_protection_cost_rwf_ha,
        "equipment_hire_cost_rwf_ha": equipment_hire_cost_rwf_ha,
        "transport_cost_rwf_ha": transport_cost_rwf_ha,
        "postharvest_cost_rwf_ha": postharvest_cost_rwf_ha,
        "storage_packaging_cost_rwf_ha": storage_packaging_cost_rwf_ha,
        "other_cost_rwf_ha": other_cost_rwf_ha, "contingency_pct": contingency_pct,
    }
    supplied_values = [area_cultivated, rainfall_mm, *inputs.values()]
    if any(value is not None and (not math.isfinite(value) or value < 0) for value in supplied_values):
        raise HTTPException(status_code=422, detail="Resource rates and prices must be non-negative")
    if contingency_pct is not None and contingency_pct > 100:
        raise HTTPException(status_code=422, detail="Contingency must be between 0 and 100 percent")
    if prices_checked_on is not None and prices_checked_on > date.today():
        raise HTTPException(status_code=422, detail="Price check date cannot be in the future")
    result = estimate_resources(area_cultivated, rainfall_mm, **inputs)
    result.update({
        "area_source": area_source,
        "rate_source": rate_source.strip() if rate_source and rate_source.strip() else None,
        "price_source": price_source.strip() if price_source and price_source.strip() else None,
        "prices_checked_on": prices_checked_on.isoformat() if prices_checked_on else None,
    })
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
        "roadmap_json": [step.model_dump(mode="json") for step in plan.roadmap],
        "resources_json": {
            **plan.resources.model_dump(),
            "plan_context": {
                "scenario": plan.scenario,
                "crop": plan.crop,
                "season": plan.season,
                "decision_context": plan.decision_context,
            },
        },
        "created_by": plan.created_by,
    }
    return crud.create_plan(record)


@router.get("/plans/{zone_id}")
def get_plans(zone_id: UUID, _: dict = Depends(require_user)):
    return crud.list_plans(zone_id)


@router.patch("/plans/{plan_id}/actions/{step_number}")
def update_plan_action(plan_id: UUID, step_number: int, payload: PlanActionStatusUpdate,
                       account: dict = Depends(require_user)):
    if step_number < 1:
        raise HTTPException(status_code=422, detail="Action number must be positive")
    if not crud.get_plan(plan_id):
        raise HTTPException(status_code=404, detail="Plan not found")
    try:
        updated = crud.update_plan_action_status(
            plan_id, step_number, payload.status, payload.change_note.strip(),
            str(account.get("account_id") or account.get("role") or "user"),
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Plan not found")
        return updated
    except HTTPException:
        raise
    except Exception as exc:
        if "Plan action was not found" in str(exc):
            raise HTTPException(status_code=404, detail="Plan action not found") from exc
        raise HTTPException(status_code=503, detail="Could not update plan action") from exc


@router.get("/plans/{plan_id}/history")
def get_plan_action_history(plan_id: UUID, step_number: int | None = Query(default=None, ge=1),
                            _: dict = Depends(require_user)):
    if not crud.get_plan(plan_id):
        raise HTTPException(status_code=404, detail="Plan not found")
    return crud.list_plan_action_history(plan_id, step_number)


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
