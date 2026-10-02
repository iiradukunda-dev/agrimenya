from fastapi import APIRouter, HTTPException
from app.models.plan import PlanCreate
from app.db import crud
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
    return crud.list_plans(zone_id)
