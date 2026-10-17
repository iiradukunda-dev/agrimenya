from datetime import datetime, timezone
from collections import Counter
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import require_admin
from app.core.config import settings
from app.db import crud
from app.models.contact import ContactCreate, ContactOut, OptInRequest, SubscriptionIn, SubscriptionOut
from app.models.whatsapp import (
    AlertApprovalOut,
    AlertDeliveryOut,
    DispatchSummary,
    TemplatePreviewOut,
    TemplatePreviewRequest,
    WhatsAppHealth,
    WhatsAppStats,
    WhatsAppTemplateOut,
)
from app.services.whatsapp.phone import mask_phone, normalize_phone
from app.services.whatsapp.dispatcher import dispatch_alert
from app.services.whatsapp.templates import TEMPLATES, approved_template, render_preview

router = APIRouter(prefix="/communication", tags=["WhatsApp"])


def _public_contact(contact: dict) -> dict:
    return {
        "id": contact["id"],
        "display_name": contact.get("display_name"),
        "role": contact.get("role"),
        "phone_masked": mask_phone(contact["phone_e164"]) if contact.get("phone_e164") else None,
        "language": contact.get("language", "en"),
        "zone_id": contact.get("zone_id"),
        "crops": contact.get("crops") or [],
        "whatsapp_opt_in": contact.get("whatsapp_opt_in", False),
        "opt_in_at": contact.get("opt_in_at"),
        "opt_in_source": contact.get("opt_in_source"),
        "opt_in_text_version": contact.get("opt_in_text_version"),
        "opt_out_at": contact.get("opt_out_at"),
        "last_inbound_at": contact.get("last_inbound_at"),
        "deleted_at": contact.get("deleted_at"),
    }


@router.post("/contacts", response_model=ContactOut, status_code=201)
def create_contact(payload: ContactCreate, _: dict = Depends(require_admin)):
    """Admin-only until role-based planner permissions are available."""
    if not payload.phone and not payload.bsuid:
        raise HTTPException(status_code=422, detail="A phone number or BSUID is required")
    phone = None
    if payload.phone:
        try:
            phone = normalize_phone(payload.phone, settings.WHATSAPP_DEFAULT_COUNTRY_CODE)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    if crud.find_contact(bsuid=payload.bsuid, phone=phone):
        raise HTTPException(status_code=409, detail="A contact with this identity already exists")
    contact = crud.create_contact({
        "display_name": payload.display_name,
        "role": payload.role,
        "phone_e164": phone,
        "bsuid": payload.bsuid,
        "language": payload.language,
        "zone_id": str(payload.zone_id) if payload.zone_id else None,
        "crops": payload.crops,
    })
    return _public_contact(contact)


@router.get("/contacts", response_model=list[ContactOut])
def list_contacts(limit: int = 200, _: dict = Depends(require_admin)):
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 500")
    return [_public_contact(contact) for contact in crud.list_contacts(limit)]


@router.post("/contacts/{contact_id}/opt-in", response_model=ContactOut)
def opt_in_contact(contact_id: str, payload: OptInRequest, _: dict = Depends(require_admin)):
    contact = crud.get_contact(contact_id)
    if not contact or contact.get("deleted_at"):
        raise HTTPException(status_code=404, detail="Contact not found")
    updated = crud.set_opt_in(contact_id, payload.source, payload.text_version)
    return _public_contact(updated)


@router.post("/contacts/{contact_id}/subscriptions", response_model=SubscriptionOut)
def subscribe_contact(contact_id: str, payload: SubscriptionIn, _: dict = Depends(require_admin)):
    contact = crud.get_contact(contact_id)
    if not contact or contact.get("deleted_at"):
        raise HTTPException(status_code=404, detail="Contact not found")
    subscription = crud.create_alert_subscription({
        "contact_id": contact_id,
        "zone_id": str(payload.zone_id) if payload.zone_id else None,
        "crop": payload.crop,
        "min_severity": payload.min_severity,
    })
    return subscription


@router.delete("/contacts/{contact_id}", response_model=ContactOut)
def delete_contact(contact_id: str, _: dict = Depends(require_admin)):
    contact = crud.get_contact(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    updated = crud.soft_delete_contact(contact_id)
    return _public_contact(updated)


@router.post("/alerts/{alert_id}/approve", response_model=AlertApprovalOut)
def approve_alert(alert_id: str, _: dict = Depends(require_admin)):
    alert = crud.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    updated = crud.update_alert(alert_id, {
        "status": "approved",
        "approved_by": "admin",
        "approved_at": datetime.now(timezone.utc).isoformat(),
    })
    return updated


@router.post("/alerts/{alert_id}/dispatch/whatsapp", status_code=status.HTTP_202_ACCEPTED, response_model=DispatchSummary)
async def dispatch_approved_alert(alert_id: str, _: dict = Depends(require_admin)):
    try:
        return await dispatch_alert(alert_id, "admin")
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/alerts/{alert_id}/delivery", response_model=AlertDeliveryOut)
def get_alert_delivery(alert_id: str, _: dict = Depends(require_admin)):
    if not crud.get_alert(alert_id):
        raise HTTPException(status_code=404, detail="Alert not found")
    counts = {key: 0 for key in ("queued", "sent", "delivered", "read", "failed")}
    for record in crud.list_alert_deliveries(alert_id):
        state = record.get("status")
        if state in counts:
            counts[state] += 1
    return {"alert_id": alert_id, "counts": counts}


@router.get("/whatsapp/health", response_model=WhatsAppHealth)
def whatsapp_health(_: dict = Depends(require_admin)):
    since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    return {"mode": settings.WHATSAPP_MODE, **crud.whatsapp_health_counts(since)}


@router.get("/whatsapp/stats", response_model=WhatsAppStats)
def whatsapp_stats(_: dict = Depends(require_admin)):
    since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    rows = crud.whatsapp_stats_rows(since)
    statuses = Counter(row.get("status", "unknown") for row in rows)
    kinds = Counter(row.get("kind", "unknown") for row in rows)
    errors = Counter(row["error_code"] for row in rows if row.get("error_code"))
    return {
        "days": 7,
        "by_status": dict(statuses),
        "by_kind": dict(kinds),
        "top_error_codes": dict(errors.most_common(5)),
    }


@router.get("/whatsapp/templates", response_model=list[WhatsAppTemplateOut])
def list_templates(_: dict = Depends(require_admin)):
    return crud.list_whatsapp_templates()


@router.post("/whatsapp/templates/{name}/{language}/preview", response_model=TemplatePreviewOut)
def preview_template(name: str, language: str, payload: TemplatePreviewRequest, _: dict = Depends(require_admin)):
    if (name, language) not in TEMPLATES:
        raise HTTPException(status_code=404, detail="WhatsApp template not found")
    try:
        preview = render_preview(name, language, payload.params)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"name": name, "language": language, "body_preview": preview}
