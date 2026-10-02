from fastapi import APIRouter

from app.db import crud
from app.models.alert import AlertCreate

router = APIRouter(prefix="/communication", tags=["Communication"])


@router.post("/alerts")
def create_alert(alert: AlertCreate):
    return crud.create_alert(alert.model_dump())


@router.get("/alerts")
def get_alerts(zone_id: str | None = None):
    return crud.list_alerts(zone_id)


@router.get("/share/{plan_id}")
def get_shareable_plan(plan_id: str):
    """
    Returns a plan formatted for sharing. Extend this to generate a PDF
    or a public read-only link once that requirement is prioritized.
    """
    plans = crud.list_plans()
    plan = next((p for p in plans if p["id"] == plan_id), None)
    return plan or {"error": "Plan not found"}
