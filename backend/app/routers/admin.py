from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.auth import require_role
from app.core.audit import audit_admin_action
from app.db import crud

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/zones")
def list_admin_zones(district: str | None = None, _: dict = Depends(require_role("admin"))):
    audit_admin_action("list_zones", "zones", {"district": district})
    return crud.list_zones(district=district)


@router.patch("/zones/{zone_id}")
def update_admin_zone(zone_id: str, payload: dict[str, Any], request: Request, _: dict = Depends(require_role("admin"))):
    zone = crud.get_zone(zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    updated = crud.update_zone(zone_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Zone update failed")
    audit_admin_action("update_zone", "zones", {"zone_id": zone_id, "changes": payload}, request=request)
    return updated


@router.delete("/zones/{zone_id}")
def delete_admin_zone(zone_id: str, request: Request, _: dict = Depends(require_role("admin"))):
    deleted = crud.delete_zone(zone_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Zone not found")
    audit_admin_action("delete_zone", "zones", {"zone_id": zone_id}, request=request)
    return deleted


@router.get("/plans")
def list_admin_plans(_: dict = Depends(require_role("admin"))):
    audit_admin_action("list_plans", "plans", {})
    return crud.list_plans()


@router.patch("/plans/{plan_id}")
def update_admin_plan(plan_id: str, payload: dict[str, Any], request: Request, _: dict = Depends(require_role("admin"))):
    plan = crud.list_plans()
    if not any(item.get("id") == plan_id for item in plan):
        raise HTTPException(status_code=404, detail="Plan not found")
    updated = crud.update_plan(plan_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Plan update failed")
    audit_admin_action("update_plan", "plans", {"plan_id": plan_id, "changes": payload}, request=request)
    return updated


@router.delete("/plans/{plan_id}")
def delete_admin_plan(plan_id: str, request: Request, _: dict = Depends(require_role("admin"))):
    deleted = crud.delete_plan(plan_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Plan not found")
    audit_admin_action("delete_plan", "plans", {"plan_id": plan_id}, request=request)
    return deleted


@router.get("/alerts")
def list_admin_alerts(_: dict = Depends(require_role("admin"))):
    audit_admin_action("list_alerts", "alerts", {})
    return crud.list_alerts()


@router.patch("/alerts/{alert_id}")
def update_admin_alert(alert_id: str, payload: dict[str, Any], request: Request, _: dict = Depends(require_role("admin"))):
    alerts = crud.list_alerts()
    if not any(item.get("id") == alert_id for item in alerts):
        raise HTTPException(status_code=404, detail="Alert not found")
    updated = crud.update_alert(alert_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Alert update failed")
    audit_admin_action("update_alert", "alerts", {"alert_id": alert_id, "changes": payload}, request=request)
    return updated


@router.delete("/alerts/{alert_id}")
def delete_admin_alert(alert_id: str, request: Request, _: dict = Depends(require_role("admin"))):
    deleted = crud.delete_alert(alert_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Alert not found")
    audit_admin_action("delete_alert", "alerts", {"alert_id": alert_id}, request=request)
    return deleted
