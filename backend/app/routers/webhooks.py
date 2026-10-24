from __future__ import annotations

import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from app.core.config import settings
from app.db import crud
from app.core.audit import audit_admin_action
from app.services.whatsapp import get_provider
from app.services.whatsapp.base import SendResult
from app.services.whatsapp.bot import handle_inbound
from app.services.whatsapp.consent import parse_keyword
from app.services.whatsapp.phone import normalize_phone

router = APIRouter(prefix="/webhooks", tags=["WhatsApp Webhooks"])
logger = logging.getLogger(__name__)
MAX_WEBHOOK_BYTES = 1_000_000
_STATUS_ORDER = {"queued": 0, "sent": 1, "delivered": 2, "read": 3, "failed": 4}


@router.get("/whatsapp", response_class=PlainTextResponse)
def verify_whatsapp_webhook(
    mode: str | None = Query(default=None, alias="hub.mode"),
    token: str | None = Query(default=None, alias="hub.verify_token"),
    challenge: str | None = Query(default=None, alias="hub.challenge"),
):
    if mode == "subscribe" and token and settings.WHATSAPP_VERIFY_TOKEN and hmac.compare_digest(
        token, settings.WHATSAPP_VERIFY_TOKEN
    ):
        return PlainTextResponse(challenge or "")
    raise HTTPException(status_code=403, detail="Webhook verification failed")


@router.post("/whatsapp")
async def receive_whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > MAX_WEBHOOK_BYTES:
        raise HTTPException(status_code=413, detail="Webhook body is too large")
    raw_chunks = bytearray()
    async for chunk in request.stream():
        if len(raw_chunks) + len(chunk) > MAX_WEBHOOK_BYTES:
            raise HTTPException(status_code=413, detail="Webhook body is too large")
        raw_chunks.extend(chunk)
    raw_body = bytes(raw_chunks)

    signature = request.headers.get("X-Hub-Signature-256", "")
    if settings.WHATSAPP_MODE == "mock" and settings.ALLOW_UNSIGNED_WEBHOOKS_IN_MOCK:
        logger.warning("Accepted an unsigned WhatsApp webhook in explicitly enabled mock mode")
    else:
        expected = "sha256=" + hmac.new(
            settings.WHATSAPP_APP_SECRET.encode("utf-8"), raw_body, hashlib.sha256
        ).hexdigest()
        if not settings.WHATSAPP_APP_SECRET or not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=403, detail="Webhook signature is invalid")

    try:
        payload = json.loads(raw_body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Webhook body must be valid JSON") from exc
    if not isinstance(payload, dict) or payload.get("object") != "whatsapp_business_account":
        return {"status": "ignored"}
    background_tasks.add_task(process_webhook, payload)
    return {"status": "accepted"}


async def process_webhook(payload: dict[str, Any]) -> None:
    for entry in payload.get("entry", []) if isinstance(payload.get("entry"), list) else []:
        changes = entry.get("changes", []) if isinstance(entry, dict) else []
        for change in changes if isinstance(changes, list) else []:
            try:
                if not isinstance(change, dict) or change.get("field") != "messages":
                    continue
                value = change.get("value") or {}
                if not isinstance(value, dict):
                    continue
                contacts = value.get("contacts") or []
                contact_info = contacts[0] if contacts and isinstance(contacts[0], dict) else {}
                for status in value.get("statuses", []) if isinstance(value.get("statuses"), list) else []:
                    try:
                        await _process_status(status)
                    except Exception as exc:
                        logger.error("WhatsApp status processing failed (%s)", type(exc).__name__)
                for message in value.get("messages", []) if isinstance(value.get("messages"), list) else []:
                    try:
                        await _process_message(message, contact_info)
                    except Exception as exc:
                        logger.error("WhatsApp message processing failed (%s)", type(exc).__name__)
            except Exception:
                logger.error("WhatsApp webhook change processing failed")


async def _process_message(message: Any, contact_info: dict[str, Any]) -> None:
    if not isinstance(message, dict) or not message.get("id"):
        return
    message_id = str(message["id"])
    message_type = str(message.get("type", "unknown"))
    if not crud.insert_webhook_event(message_id, f"inbound:{message_type}"):
        return

    phone = _normalize_webhook_phone(message.get("from") or contact_info.get("wa_id"))
    bsuid = contact_info.get("user_id") or contact_info.get("bsuid")
    contact = crud.find_contact(bsuid=str(bsuid) if bsuid else None, phone=phone)
    if not contact and (phone or bsuid):
        profile = contact_info.get("profile") or {}
        contact = crud.create_contact({
            "phone_e164": phone,
            "bsuid": str(bsuid) if bsuid else None,
            "display_name": profile.get("name"),
            "whatsapp_opt_in": False,
        })
    if not contact:
        logger.info("Ignored inbound WhatsApp message without a resolvable identity")
        return
    if bsuid and contact.get("bsuid") != str(bsuid):
        duplicate_identity = crud.find_contact(bsuid=str(bsuid))
        if duplicate_identity and str(duplicate_identity.get("id")) != str(contact.get("id")):
            contact = crud.merge_contacts(contact["id"], duplicate_identity["id"], phone, str(bsuid)) or contact
        else:
            contact = crud.update_contact(contact["id"], {"bsuid": str(bsuid)}) or contact

    inbound_at = datetime.now(timezone.utc).isoformat()
    crud.touch_inbound(contact["id"], inbound_at)
    text = _message_text(message)
    crud.create_message_log({
        "direction": "inbound",
        "contact_id": contact["id"],
        "wa_message_id": message_id,
        "kind": "bot_reply",
        "status": "received",
        "body_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    })

    system = message.get("system")
    if isinstance(system, dict) and system.get("type") == "user_changed_number":
        await _update_changed_number(contact, system)
        return

    keyword = parse_keyword(text)
    if keyword == "STOP":
        first_opt_out = contact.get("opt_out_at") is None
        crud.set_opt_out(contact["id"])
        if first_opt_out:
            confirmation = (
                "Ntuzongera kwakira amatangazo ya Agri-Menya kuri WhatsApp. Ohereza EMERA niba ushaka kongera kuyemera."
                if contact.get("language") == "rw"
                else "You are unsubscribed from Agri-Menya WhatsApp alerts. Reply START to opt in again."
            )
            await _send_logged_reply(contact, confirmation, "optout_confirm")
        return
    if keyword == "START":
        crud.set_opt_in(contact["id"], "whatsapp_keyword", "whatsapp-keyword-v1")
        confirmation = (
            "Wemeye kwakira amatangazo ya Agri-Menya kuri WhatsApp. Ohereza SHIRA kugira ngo uyahagarike."
            if contact.get("language") == "rw"
            else "You are subscribed to Agri-Menya WhatsApp alerts. Reply STOP to unsubscribe."
        )
        await _send_logged_reply(contact, confirmation, "optin_confirm")
        return

    if text:
        reply = handle_inbound(contact, text)
        if reply:
            await _send_logged_reply(contact, reply, "bot_reply")
    elif message_type not in {"text", "button", "interactive"}:
        since = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        if not crud.has_recent_message(contact["id"], "bot_reply", since):
            await _send_logged_reply(contact, "Please send a text message; this number cannot process media yet.", "bot_reply")


async def _process_status(status: Any) -> None:
    if not isinstance(status, dict) or not status.get("id") or not status.get("status"):
        return
    message_id = str(status["id"])
    state = str(status["status"]).lower()
    if state not in _STATUS_ORDER:
        return
    event_key = f"{message_id}:{state}"
    if not crud.insert_webhook_event(event_key, f"status:{state}"):
        return
    record = crud.get_message_by_wa_id(message_id)
    if not record:
        return
    current = str(record.get("status", "queued"))
    update: dict[str, Any] = {}
    if current not in {"delivered", "read"} and _STATUS_ORDER[state] >= _STATUS_ORDER.get(current, 0):
        update["status"] = state
    errors = status.get("errors") or []
    if state == "failed" and errors and isinstance(errors[0], dict):
        update["error_code"] = str(errors[0].get("code") or "unknown")
        update["error_detail"] = str(errors[0].get("title") or "Delivery failed")[:200]
        if str(errors[0].get("code")) == "131026" and record.get("contact_id"):
            crud.increment_contact_undeliverable(record["contact_id"])
    if update:
        crud.update_message_log(record["id"], update)


async def _send_logged_reply(contact: dict[str, Any], body: str, kind: str) -> SendResult:
    address = contact.get("phone_e164") or contact.get("bsuid")
    record = crud.create_message_log({
        "direction": "outbound",
        "contact_id": contact["id"],
        "kind": kind,
        "status": "queued",
        "body_hash": hashlib.sha256(body.encode("utf-8")).hexdigest(),
    })
    if not address:
        crud.update_message_log(record["id"], {"status": "failed", "error_code": "missing_address"})
        return SendResult(False, error_code="missing_address")
    try:
        result = await get_provider().send_text(address, body)
    except Exception as exc:
        logger.error("WhatsApp confirmation provider failed (%s)", type(exc).__name__)
        result = SendResult(False, error_code="provider_error", error_detail="Provider unavailable")
    update: dict[str, Any] = {"status": "queued" if result.ok else "failed"}
    if result.wa_message_id:
        update["wa_message_id"] = result.wa_message_id
    if result.error_code:
        update["error_code"] = result.error_code
        update["error_detail"] = result.error_detail
    crud.update_message_log(record["id"], update)
    return result


async def _update_changed_number(contact: dict[str, Any], system: dict[str, Any]) -> None:
    new_phone = _normalize_webhook_phone(system.get("wa_id") or system.get("new_wa_id"))
    new_bsuid = system.get("user_id") or system.get("bsuid")
    if not new_phone and not new_bsuid:
        logger.info("Ignored WhatsApp identity update without a new identifier")
        return
    duplicate = crud.find_contact(bsuid=str(new_bsuid) if new_bsuid else None, phone=new_phone)
    if duplicate and str(duplicate.get("id")) != str(contact.get("id")):
        updated = crud.merge_contacts(contact["id"], duplicate["id"], new_phone, str(new_bsuid) if new_bsuid else None)
    else:
        updated = crud.update_contact(contact["id"], {
            "phone_e164": new_phone or contact.get("phone_e164"),
            "bsuid": str(new_bsuid) if new_bsuid else contact.get("bsuid"),
        })
    from app.services.whatsapp.phone import mask_phone
    audit_admin_action("whatsapp_number_changed", "contact", {
        "contact_id": str((updated or contact).get("id")),
        "old_phone": mask_phone(contact["phone_e164"]) if contact.get("phone_e164") else None,
        "new_phone": mask_phone(new_phone) if new_phone else None,
    })


def _normalize_webhook_phone(value: Any) -> str | None:
    if not value:
        return None
    try:
        return normalize_phone(str(value), settings.WHATSAPP_DEFAULT_COUNTRY_CODE)
    except ValueError:
        return None


def _message_text(message: dict[str, Any]) -> str:
    message_type = message.get("type")
    if message_type == "text":
        return str((message.get("text") or {}).get("body") or "")
    if message_type == "button":
        button = message.get("button") or {}
        return str(button.get("text") or button.get("payload") or "")
    if message_type == "interactive":
        interactive = message.get("interactive") or {}
        button_reply = interactive.get("button_reply") or {}
        list_reply = interactive.get("list_reply") or {}
        return str(button_reply.get("title") or button_reply.get("id") or list_reply.get("title") or list_reply.get("id") or "")
    return ""
