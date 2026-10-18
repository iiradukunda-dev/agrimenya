from __future__ import annotations

import asyncio
import hashlib
import re
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.core.config import settings
from app.db import crud
from app.services.whatsapp import get_provider
from app.services.whatsapp.templates import approved_template, validate_params


def sanitize_alert_text(text: str, allow_links: bool = False) -> str:
    clean = "".join(character for character in str(text or "") if character.isprintable())
    clean = re.sub(r"\s+", " ", clean).strip()
    if not allow_links:
        clean = re.sub(r"https?://\S+|www\.\S+", "", clean, flags=re.IGNORECASE)
        clean = re.sub(r"(?<!\w)(?:\+?\d[\d ()-]{7,}\d)(?!\w)", "", clean)
        clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:280]


async def dispatch_alert(alert_id: UUID | str, approved_by: str) -> dict[str, Any]:
    alert = crud.get_alert(alert_id)
    if not alert:
        raise LookupError("Alert not found")
    if alert.get("status") != "approved":
        raise PermissionError("Alert must be approved before WhatsApp dispatch")
    zone = crud.get_zone(alert["zone_id"]) if alert.get("zone_id") else None
    if not zone:
        raise LookupError("Alert zone not found")

    crop = alert.get("crop") or "Unknown"
    candidates = crud.list_contacts_for_alert(alert["zone_id"], crop if crop != "Unknown" else None, alert.get("severity", "Info"))
    summary: dict[str, Any] = {
        "queued": 0,
        "sent": 0,
        "failed": 0,
        "skipped_no_consent": 0,
        "skipped_no_template": 0,
        "skipped_daily_cap": 0,
        "by_error_code": {},
    }
    semaphore = asyncio.Semaphore(5)
    rate_limit_streak = 0
    for offset in range(0, len(candidates), 5):
        batch = candidates[offset:offset + 5]
        outcomes = await asyncio.gather(*(
            _dispatch_one(alert, zone, contact, crop, semaphore) for contact in batch
        ))
        for outcome in outcomes:
            for key, count in outcome.items():
                if key != "error_code" and key in summary:
                    summary[key] += count
            error_code = outcome.get("error_code")
            if error_code:
                summary["by_error_code"][error_code] = summary["by_error_code"].get(error_code, 0) + 1
                rate_limit_streak = rate_limit_streak + 1 if error_code in {"131048", "130429"} else 0
            else:
                rate_limit_streak = 0
        if rate_limit_streak >= 3:
            break
    return summary


async def _dispatch_one(alert: dict, zone: dict, contact: dict, crop: str, semaphore: asyncio.Semaphore) -> dict[str, Any]:
    contact_id = contact["id"]
    if not contact.get("whatsapp_opt_in") or contact.get("opt_out_at") or contact.get("deleted_at"):
        return {"skipped_no_consent": 1}
    address = contact.get("phone_e164") or contact.get("bsuid")
    if not address:
        return {"skipped_no_consent": 1}
    existing = crud.get_alert_contact_delivery(alert["id"], contact_id)
    if existing:
        return {"queued": 1} if existing.get("status") in {"queued", "sent", "delivered", "read"} else {"failed": 1}

    midnight = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    if crud.count_outbound_messages_since(contact_id, midnight) >= settings.WHATSAPP_DAILY_CAP:
        return {"skipped_daily_cap": 1}

    message = sanitize_alert_text(alert.get("message", ""), bool(alert.get("allow_links"))) or "No additional details"
    action = sanitize_alert_text(alert.get("action") or "", bool(alert.get("allow_links"))) or "Follow local extension guidance"
    district = str(zone.get("district") or "Unknown")
    last_inbound = _parse_timestamp(contact.get("last_inbound_at"))
    within_window = bool(last_inbound and (datetime.now(timezone.utc) - last_inbound).total_seconds() < 86400)
    template = None
    params: list[str] | None = None
    if not within_window:
        template = approved_template("agrimenya_alert", contact.get("language", "en"))
        if not template:
            crud.create_message_log({
                "direction": "outbound", "contact_id": contact_id,
                "kind": "alert", "alert_id": alert["id"],
                "status": "failed", "error_code": "no_approved_template",
                "body_hash": hashlib.sha256(message.encode("utf-8")).hexdigest(),
            })
            return {"skipped_no_template": 1, "error_code": "no_approved_template"}
        language = str(template["language"])
        params = validate_params("agrimenya_alert", [district, crop, message or "No additional details", action])
    body = (
        f"Agri-Menya alert for {district} ({crop}): {message} Suggested action: {action}. "
        "Reply STOP to unsubscribe."
    )
    record = crud.create_message_log({
        "direction": "outbound", "contact_id": contact_id,
        "kind": "alert", "alert_id": alert["id"],
        "template_name": template["name"] if template else None,
        "status": "queued",
        "body_hash": hashlib.sha256((body if within_window else "\x1f".join(params or [])).encode("utf-8")).hexdigest(),
    })
    async with semaphore:
        provider = get_provider()
        result = (
            await provider.send_text(address, body)
            if within_window
            else await provider.send_template(address, template["name"], language, params or [])
        )
        await asyncio.sleep(0.1)
    update: dict[str, Any] = {}
    if result.ok:
        if result.wa_message_id:
            update["wa_message_id"] = result.wa_message_id
        outcome = {"queued": 1}
    else:
        update["status"] = "failed"
        update["error_code"] = result.error_code or "provider_error"
        update["error_detail"] = result.error_detail or "Provider rejected message"
        outcome = {"failed": 1, "error_code": update["error_code"]}
    if update:
        crud.update_message_log(record["id"], update)
    return outcome


def _parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed
    except (TypeError, ValueError):
        return None
