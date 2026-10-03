from fastapi import APIRouter, HTTPException
from app.models.plan import PlanCreate
from app.db import crud
from app.services.disease_detector import detect_crop_disease
from app.services.resource_estimator import estimate_resources

router = APIRouter(prefix="/planification", tags=["Planification"])


@router.get("/resources/{zone_id}")
def get_resource_estimate(zone_id: str, area_cultivated: float | None = None,
                           rainfall_mm: float | None = None):
    return estimate_resources(area_cultivated, rainfall_mm)


@router.post("/roadmap")
def create_roadmap(plan: PlanCreate):
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
def get_plans(zone_id: str):
    try:
        return crud.list_plans(zone_id)
    except HTTPException as exc:
        if exc.status_code == 503:
            return []
        raise


@router.post("/disease-plan")
def create_disease_plan(zone_id: str, crop: str, symptoms: str, image_description: str | None = None):
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
        "roadmap": [
            "Inspect affected plants in the affected zone and mark the spread area.",
            "Apply the recommended treatment plan within 24 hours.",
            "Schedule a follow-up field visit after 7 days to confirm disease suppression.",
        ],
    }
