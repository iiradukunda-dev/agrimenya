"""
All direct Supabase table access lives here. Routers and services call
these functions rather than touching the Supabase client directly -
keeps query logic in one place if the schema changes.
"""
from uuid import UUID
import logging
import time
from datetime import datetime, timezone
from fastapi import HTTPException
import httpx
from postgrest import exceptions as postgrest_exceptions
from app.core.supabase_client import get_supabase


def get_admin_account_by_email(email: str) -> dict | None:
    rows = _exec_query_get_data(
        get_supabase().table("admin_accounts").select("*").eq("email", email.lower()).limit(1)
    )
    return rows[0] if rows else None


def get_admin_account_by_id(account_id: str) -> dict | None:
    rows = _exec_query_get_data(
        get_supabase().table("admin_accounts").select("*").eq("id", account_id).limit(1)
    )
    return rows[0] if rows else None


def get_community_account_by_email(email: str) -> dict | None:
    rows = _exec_query_get_data(
        get_supabase().table("community_accounts").select("*")
        .eq("email", email.lower()).limit(1)
    )
    return rows[0] if rows else None


def get_community_account_by_id(account_id: str) -> dict | None:
    rows = _exec_query_get_data(
        get_supabase().table("community_accounts").select("*")
        .eq("id", account_id).limit(1)
    )
    return rows[0] if rows else None


def create_community_account(email: str, display_name: str, password_hash: str) -> dict:
    result = get_supabase().table("community_accounts").insert({
        "email": email.lower(), "display_name": display_name, "password_hash": password_hash,
    }).execute()
    return result.data[0]


def list_community_accounts(limit: int = 200) -> list[dict]:
    return _exec_query_get_data(
        get_supabase().table("community_accounts")
        .select("id,email,display_name,role,is_active,created_at")
        .order("created_at", desc=True).limit(max(1, min(int(limit), 500)))
    )


def list_active_community_emails(limit: int = 10000) -> list[str]:
    maximum = max(1, min(int(limit), 100000))
    rows = []
    for offset in range(0, maximum, 1000):
        page = _exec_query_get_data(
            get_supabase().table("community_accounts").select("email")
            .eq("is_active", True).order("created_at").range(offset, min(offset + 999, maximum - 1))
        )
        rows.extend(page)
        if len(page) < 1000:
            break
    emails = []
    seen = set()
    for row in rows:
        email = str(row.get("email") or "").strip()
        key = email.casefold()
        if email and key not in seen:
            seen.add(key)
            emails.append(email)
    return emails


def set_community_account_active(account_id: str, is_active: bool) -> bool:
    account = get_community_account_by_id(account_id)
    if not account:
        return False
    result = get_supabase().table("community_accounts").update({
        "is_active": is_active,
        "session_version": int(account.get("session_version", 1)) + 1,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", account_id).execute()
    return bool(result.data)


def create_community_post(author_id: str, title: str, body: str) -> dict:
    result = get_supabase().table("community_posts").insert({
        "author_id": author_id, "title": title, "body": body,
    }).execute()
    return result.data[0]


def list_community_posts(limit: int = 30, offset: int = 0) -> list[dict]:
    return _exec_query_get_data(
        get_supabase().table("community_posts")
        .select("id,title,body,author_id,status,created_at,updated_at,author:community_accounts(display_name,role)")
        .eq("status", "published").order("created_at", desc=True)
        .range(offset, offset + limit - 1)
    )


def get_community_post(post_id: str) -> dict | None:
    rows = _exec_query_get_data(
        get_supabase().table("community_posts").select("id,status,author_id")
        .eq("id", post_id).limit(1)
    )
    return rows[0] if rows else None


def create_community_comment(post_id: str, author_id: str, body: str) -> dict:
    result = get_supabase().table("community_comments").insert({
        "post_id": post_id, "author_id": author_id, "body": body,
    }).execute()
    return result.data[0]


def get_community_comment(comment_id: str) -> dict | None:
    rows = _exec_query_get_data(
        get_supabase().table("community_comments").select("id,post_id,author_id,status")
        .eq("id", comment_id).limit(1)
    )
    return rows[0] if rows else None


def list_community_comments(post_id: str, limit: int = 100) -> list[dict]:
    return _exec_query_get_data(
        get_supabase().table("community_comments")
        .select("id,post_id,body,author_id,status,created_at,author:community_accounts(display_name,role)")
        .eq("post_id", post_id).eq("status", "published")
        .order("created_at").limit(max(1, min(int(limit), 200)))
    )


def create_community_report(reporter_id: str, *, reason: str,
                            post_id: str | None = None, comment_id: str | None = None) -> dict:
    result = get_supabase().table("community_reports").insert({
        "reporter_id": reporter_id, "reason": reason,
        "post_id": post_id, "comment_id": comment_id,
    }).execute()
    return result.data[0]


def list_community_reports(limit: int = 100) -> list[dict]:
    return _exec_query_get_data(
        get_supabase().table("community_reports")
        .select("id,reporter_id,post_id,comment_id,reason,status,created_at,"
                "post:community_posts(title,body,author:community_accounts(display_name)),"
                "comment:community_comments(body,author:community_accounts(display_name))")
        .eq("status", "open").order("created_at").limit(max(1, min(int(limit), 200)))
    )


def moderate_community_content(*, target_kind: str, target_id: str, status: str) -> bool:
    table = "community_posts" if target_kind == "post" else "community_comments"
    result = get_supabase().table(table).update({
        "status": status, "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", target_id).execute()
    return bool(result.data)


def resolve_community_report(report_id: str, reviewer_id: str | None, status: str) -> bool:
    result = get_supabase().table("community_reports").update({
        "status": status, "reviewed_by": reviewer_id,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", report_id).eq("status", "open").execute()
    return bool(result.data)


def create_admin_account(email: str, display_name: str, password_hash: str) -> dict:
    result = get_supabase().table("admin_accounts").insert({
        "email": email.lower(), "display_name": display_name, "password_hash": password_hash,
    }).execute()
    return result.data[0]


def list_admin_accounts() -> list[dict]:
    return _exec_query_get_data(
        get_supabase().table("admin_accounts")
        .select("id,email,display_name,is_active,created_at,updated_at,last_login_at")
        .order("created_at")
    )


def set_admin_account_active(account_id: str, is_active: bool) -> None:
    account = get_admin_account_by_id(account_id)
    if not account:
        return
    changes = {
        "is_active": is_active,
        "session_version": int(account.get("session_version", 1)) + 1,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    get_supabase().table("admin_accounts").update(changes).eq("id", account_id).execute()


def record_admin_login(account_id: str) -> None:
    get_supabase().table("admin_accounts").update({"last_login_at": datetime.now(timezone.utc).isoformat()}).eq("id", account_id).execute()


def update_admin_password(account_id: str, password_hash: str) -> None:
    account = get_admin_account_by_id(account_id)
    if not account:
        return
    get_supabase().table("admin_accounts").update({
        "password_hash": password_hash, "session_version": int(account.get("session_version", 1)) + 1,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", account_id).execute()


def increment_admin_session_version(account_id: str) -> None:
    account = get_admin_account_by_id(account_id)
    if account:
        get_supabase().table("admin_accounts").update({
            "session_version": int(account.get("session_version", 1)) + 1,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", account_id).execute()


def create_admin_password_reset_token(account_id: str, token_hash: str, expires_at: str) -> None:
    table = get_supabase().table("admin_password_reset_tokens")
    table.update({"used_at": datetime.now(timezone.utc).isoformat()}).eq("admin_id", account_id).is_("used_at", "null").execute()
    table.insert({"admin_id": account_id, "token_hash": token_hash, "expires_at": expires_at}).execute()


def consume_admin_password_reset_token(token_hash: str) -> dict | None:
    now = datetime.now(timezone.utc).isoformat()
    rows = _exec_query_get_data(
        get_supabase().table("admin_password_reset_tokens").update({"used_at": now})
        .eq("token_hash", token_hash).is_("used_at", "null").gt("expires_at", now)
        .select("admin_id")
    )
    return rows[0] if rows else None


def invalidate_admin_password_reset_tokens(account_id: str) -> None:
    get_supabase().table("admin_password_reset_tokens").update({
        "used_at": datetime.now(timezone.utc).isoformat(),
    }).eq("admin_id", account_id).is_("used_at", "null").execute()


def create_nisr_import(payload: dict) -> dict:
    result = get_supabase().table("nisr_imports").insert(payload).execute()
    return result.data[0]


def find_nisr_import_by_hash(digest: str) -> dict | None:
    rows = _exec_query_get_data(
        get_supabase().table("nisr_imports").select("id,status").eq("sha256", digest).limit(1)
    )
    return rows[0] if rows else None


def insert_nisr_yield_records(records: list[dict]) -> None:
    table = get_supabase().table("nisr_yield_records")
    for offset in range(0, len(records), 500):
        table.insert(records[offset:offset + 500]).execute()


def finish_nisr_import(import_id: str, status: str, **fields) -> dict | None:
    result = get_supabase().table("nisr_imports").update({"status": status, **fields}).eq("id", import_id).execute()
    return result.data[0] if result.data else None


def delete_nisr_yield_records(import_id: str) -> None:
    get_supabase().table("nisr_yield_records").delete().eq("import_id", import_id).execute()


def list_nisr_imports(limit: int = 100) -> list[dict]:
    return _exec_query_get_data(
        get_supabase().table("nisr_imports").select(
            "id,source_filename,source_release,season,sha256,status,row_count,imported_by,created_at,activated_at"
        ).order("created_at", desc=True).limit(max(1, min(int(limit), 200)))
    )


def get_yield_evidence(district: str | None, crop: str) -> list[dict]:
    """Read current NISR imports first, then the existing database survey rows."""
    sb = get_supabase()
    try:
        imports = _exec_query_get_data(
            sb.table("nisr_imports").select("id,season,activated_at")
            .eq("status", "active").order("activated_at", desc=True)
        )
    except HTTPException:
        # Keep baseline reads available before migration 0007 has been applied.
        imports = []
    # A corrected release supersedes the older import for that same season.
    newest_by_season: dict[str, dict] = {}
    for item in imports:
        newest_by_season.setdefault(str(item.get("season", "")).casefold(), item)
    import_ids = [item["id"] for item in newest_by_season.values() if item.get("id")]
    if import_ids:
        query = sb.table("nisr_yield_records").select(
            "district,crop,season,yield_kg_ha,production_mt,cultivated_area_ha,import_id"
        ).eq("crop", crop).in_("import_id", import_ids)
        if district:
            query = query.eq("district", district)
        imported = _exec_query_get_all(query)
    else:
        imported = []

    # Compatibility for the 2026 SAS rows already stored in agri_metrics.
    zones = list_zones(district=district) if district else list_zones()
    zone_ids = [str(zone["id"]) for zone in zones if zone.get("id")]
    rows = []
    if zone_ids:
        query = sb.table("agri_metrics").select(
            "yield_actual,production_mt,area_cultivated,season,zone_id,zones(district)"
        ).eq("crop", crop).in_("zone_id", zone_ids)
        rows = _exec_query_get_all(query)
    legacy = [{
        "district": (row.get("zones") or {}).get("district"),
        "crop": crop,
        "season": row.get("season"),
        "yield_kg_ha": row.get("yield_actual"),
        "production_mt": row.get("production_mt"),
        "cultivated_area_ha": row.get("area_cultivated"),
    } for row in rows]
    imported_keys = {(str(row.get("district", "")).casefold(), str(row.get("crop", "")).casefold(), str(row.get("season", "")).casefold()) for row in imported}
    return imported + [row for row in legacy if (
        str(row.get("district", "")).casefold(), str(row.get("crop", "")).casefold(),
        str(row.get("season", "")).casefold()
    ) not in imported_keys]


def get_yield_crop_names() -> list[str]:
    sb = get_supabase()
    names: set[str] = set()
    try:
        imports = [item["id"] for item in list_nisr_imports(200) if item.get("status") == "active"]
        records = (_exec_query_get_data(
            sb.table("nisr_yield_records").select("crop,import_id").in_("import_id", imports).limit(1000)
        ) if imports else [])
        names.update(str(row["crop"]) for row in records if row.get("crop"))
    except HTTPException:
        pass
    metrics = _exec_query_get_data(sb.table("agri_metrics").select("crop").limit(1000))
    names.update(str(row["crop"]) for row in metrics if row.get("crop"))
    return sorted(names, key=str.casefold)


def get_district_yield_evidence(district: str) -> list[dict]:
    """Return current imported and legacy yield records for one district."""
    sb = get_supabase()
    try:
        imports = _exec_query_get_data(
            sb.table("nisr_imports").select("id,season,activated_at")
            .eq("status", "active").order("activated_at", desc=True)
        )
    except HTTPException:
        imports = []
    newest_by_season: dict[str, dict] = {}
    for item in imports:
        newest_by_season.setdefault(str(item.get("season", "")).casefold(), item)
    import_ids = [item["id"] for item in newest_by_season.values() if item.get("id")]
    imported = []
    if import_ids:
        imported = _exec_query_get_all(
            sb.table("nisr_yield_records").select(
                "district,crop,season,yield_kg_ha,production_mt,cultivated_area_ha,import_id"
            ).eq("district", district).in_("import_id", import_ids)
        )
    zones = list_zones(district=district)
    zone_ids = [str(zone["id"]) for zone in zones if zone.get("id")]
    legacy = []
    if zone_ids:
        rows = _exec_query_get_all(
            sb.table("agri_metrics").select(
                "crop,season,yield_actual,production_mt,area_cultivated,zone_id"
            ).in_("zone_id", zone_ids)
        )
        legacy = [{
            "district": district, "crop": row.get("crop"), "season": row.get("season"),
            "yield_kg_ha": row.get("yield_actual"), "production_mt": row.get("production_mt"),
            "cultivated_area_ha": row.get("area_cultivated"),
        } for row in rows]
    imported_keys = {(str(row.get("crop", "")).casefold(), str(row.get("season", "")).casefold()) for row in imported}
    return imported + [row for row in legacy if (
        str(row.get("crop", "")).casefold(), str(row.get("season", "")).casefold()
    ) not in imported_keys]


def create_contact(contact: dict) -> dict:
    result = get_supabase().table("contacts").insert(contact).execute()
    return result.data[0]


def get_contact(contact_id: UUID | str) -> dict | None:
    rows = _exec_query_get_data(
        get_supabase().table("contacts").select("*").eq("id", str(contact_id)).limit(1)
    )
    return rows[0] if rows else None


def find_contact(bsuid: str | None = None, phone: str | None = None) -> dict | None:
    sb = get_supabase()
    if bsuid:
        rows = _exec_query_get_data(
            sb.table("contacts").select("*").eq("bsuid", bsuid).limit(1)
        )
        if rows:
            return rows[0]
    if phone:
        rows = _exec_query_get_data(
            sb.table("contacts").select("*").eq("phone_e164", phone).limit(1)
        )
        return rows[0] if rows else None
    return None


def update_contact(contact_id: UUID | str, payload: dict) -> dict | None:
    return _update_record("contacts", contact_id, payload)


def set_opt_in(contact_id: UUID | str, source: str, text_version: str) -> dict | None:
    from datetime import datetime, timezone

    return update_contact(contact_id, {
        "whatsapp_opt_in": True,
        "opt_in_at": datetime.now(timezone.utc).isoformat(),
        "opt_in_source": source,
        "opt_in_text_version": text_version,
        "opt_out_at": None,
    })


def set_opt_out(contact_id: UUID | str) -> dict | None:
    from datetime import datetime, timezone

    return update_contact(contact_id, {
        "whatsapp_opt_in": False,
        "opt_out_at": datetime.now(timezone.utc).isoformat(),
    })


def touch_inbound(contact_id: UUID | str, timestamp: str | None = None) -> dict | None:
    from datetime import datetime, timezone

    return update_contact(contact_id, {
        "last_inbound_at": timestamp or datetime.now(timezone.utc).isoformat(),
    })


def soft_delete_contact(contact_id: UUID | str) -> dict | None:
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()
    return update_contact(contact_id, {
        "display_name": None,
        "phone_e164": None,
        "bsuid": None,
        "whatsapp_opt_in": False,
        "opt_out_at": now,
        "deleted_at": now,
        "updated_at": now,
    })


def list_contacts(limit: int = 200) -> list[dict]:
    query = get_supabase().table("contacts").select("*").is_("deleted_at", "null")
    return _exec_query_get_data(query.order("created_at", desc=True).limit(max(1, min(limit, 500))))


def list_contacts_for_alert(zone_id: UUID | str, crop: str | None, severity: str) -> list[dict]:
    severity_order = {"info": 0, "warning": 1, "critical": 2}
    required = severity_order.get(str(severity).lower())
    if required is None:
        return []
    subscriptions = _exec_query_get_data(
        get_supabase().table("alert_subscriptions").select("contact_id,zone_id,crop,min_severity")
    )
    matching_ids = {
        str(item["contact_id"])
        for item in subscriptions
        if (item.get("zone_id") is None or str(item.get("zone_id")) == str(zone_id))
        and (item.get("crop") is None or item.get("crop") == crop)
        and severity_order.get(str(item.get("min_severity", "warning")).lower(), 3) <= required
    }
    if not matching_ids:
        return []
    rows = _exec_query_get_data(
        get_supabase().table("contacts").select("*")
        .in_("id", list(matching_ids))
        .eq("whatsapp_opt_in", True)
        .is_("opt_out_at", "null")
        .is_("deleted_at", "null")
    )
    return rows


def create_alert_subscription(subscription: dict) -> dict:
    table = get_supabase().table("alert_subscriptions")
    query = table.select("*").eq("contact_id", str(subscription["contact_id"]))
    query = query.is_("zone_id", "null") if subscription.get("zone_id") is None else query.eq("zone_id", str(subscription["zone_id"]))
    query = query.is_("crop", "null") if subscription.get("crop") is None else query.eq("crop", subscription["crop"])
    existing = _exec_query_get_data(query.limit(1))
    if existing:
        updated = table.update({"min_severity": subscription.get("min_severity", "warning")})
        result = updated.eq("id", existing[0]["id"]).execute()
        return result.data[0]
    result = table.insert(subscription).execute()
    return result.data[0]


def list_alert_subscriptions(contact_id: UUID | str) -> list[dict]:
    return _exec_query_get_data(
        get_supabase().table("alert_subscriptions").select("*")
        .eq("contact_id", str(contact_id))
    )


def merge_contacts(contact_id: UUID | str, duplicate_id: UUID | str, phone: str | None, bsuid: str | None) -> dict | None:
    survivor = get_contact(contact_id)
    duplicate = get_contact(duplicate_id)
    if not survivor or not duplicate:
        return None
    if str(survivor.get("created_at", "")) > str(duplicate.get("created_at", "")):
        survivor, duplicate = duplicate, survivor

    subscriptions = list_alert_subscriptions(duplicate["id"])
    sb = get_supabase()
    survivor_subscriptions = list_alert_subscriptions(survivor["id"])
    for subscription in subscriptions:
        if any(
            existing.get("zone_id") == subscription.get("zone_id")
            and existing.get("crop") == subscription.get("crop")
            for existing in survivor_subscriptions
        ):
            continue
        subscription_payload = {
            "contact_id": survivor["id"],
            "zone_id": subscription.get("zone_id"),
            "crop": subscription.get("crop"),
            "min_severity": subscription.get("min_severity", "warning"),
        }
        sb.table("alert_subscriptions").insert(subscription_payload).execute()
    sb.table("alert_subscriptions").delete().eq("contact_id", str(duplicate["id"])).execute()
    sb.table("message_log").update({"contact_id": str(survivor["id"])}).eq("contact_id", str(duplicate["id"])).execute()

    opt_out_at = survivor.get("opt_out_at") or duplicate.get("opt_out_at")
    opt_in_record = survivor if survivor.get("whatsapp_opt_in") else duplicate
    sb.table("contacts").update({
        "phone_e164": None,
        "bsuid": None,
        "deleted_at": datetime.now(timezone.utc).isoformat(),
        "whatsapp_opt_in": False,
    }).eq("id", str(duplicate["id"])).execute()
    return update_contact(survivor["id"], {
        "display_name": survivor.get("display_name") or duplicate.get("display_name"),
        "phone_e164": phone or survivor.get("phone_e164"),
        "bsuid": bsuid or survivor.get("bsuid"),
        "whatsapp_opt_in": bool(opt_in_record.get("whatsapp_opt_in")) and not bool(opt_out_at),
        "opt_in_at": opt_in_record.get("opt_in_at"),
        "opt_in_source": opt_in_record.get("opt_in_source"),
        "opt_in_text_version": opt_in_record.get("opt_in_text_version"),
        "opt_out_at": opt_out_at,
    })


def create_message_log(record: dict) -> dict:
    result = get_supabase().table("message_log").insert(record).execute()
    return result.data[0]


def update_message_log(message_id: UUID | str, payload: dict) -> dict | None:
    return _update_record("message_log", message_id, payload)


def get_message_by_wa_id(wa_message_id: str) -> dict | None:
    rows = _exec_query_get_data(
        get_supabase().table("message_log").select("*").eq("wa_message_id", wa_message_id).limit(1)
    )
    return rows[0] if rows else None


def has_recent_message(contact_id: UUID | str, kind: str, since: str) -> bool:
    rows = _exec_query_get_data(
        get_supabase().table("message_log").select("id")
        .eq("contact_id", str(contact_id)).eq("kind", kind)
        .eq("direction", "outbound")
        .gte("created_at", since).limit(1)
    )
    return bool(rows)


def increment_contact_undeliverable(contact_id: UUID | str) -> dict | None:
    contact = get_contact(contact_id)
    if not contact:
        return None
    return update_contact(contact_id, {
        "undeliverable_count": int(contact.get("undeliverable_count") or 0) + 1,
    })


def count_inbound_messages_since(contact_id: UUID | str, since: str, limit: int = 21) -> int:
    rows = _exec_query_get_data(
        get_supabase().table("message_log").select("id")
        .eq("contact_id", str(contact_id)).eq("direction", "inbound")
        .gte("created_at", since).limit(max(1, min(limit, 100)))
    )
    return len(rows)


def list_district_crops() -> list[str]:
    return get_yield_crop_names()


def insert_webhook_event(event_key: str, payload_type: str) -> bool:
    result = get_supabase().table("webhook_events").upsert(
        {"event_key": event_key, "payload_type": payload_type},
        on_conflict="event_key",
        ignore_duplicates=True,
    ).select("event_key").execute()
    return bool(result.data)


def _exec_query_get_data(query, max_retries: int = 3, backoff: float = 0.5):
    """Execute a PostgREST query with defensive error handling and retry.

    Retries transient network errors with exponential backoff. All
    exceptions are logged with repr() to aid debugging without leaking
    credential values.
    """
    attempt = 0
    while True:
        try:
            return query.execute().data
        except postgrest_exceptions.APIError as e:
            logging.exception("Supabase API error (no retry): %r", e)
            raise HTTPException(status_code=503, detail="Database request failed")
        except (httpx.ConnectError, httpx.ReadError, httpx.ConnectTimeout) as e:
            attempt += 1
            logging.warning("Transient network error connecting to Supabase (attempt %d/%d): %r", attempt, max_retries, e)
            if attempt >= max_retries:
                logging.exception("Max retries reached for Supabase network error: %r", e)
                raise HTTPException(status_code=503, detail="Network error connecting to Supabase")
            sleep_for = backoff * (2 ** (attempt - 1))
            time.sleep(sleep_for)
            continue
        except Exception as e:
            logging.exception("Unexpected error executing Supabase query: %r", e)
            raise HTTPException(status_code=503, detail="Unexpected error connecting to the database")


def _exec_query_get_all(query, page_size: int = 500, max_pages: int = 100) -> list[dict]:
    """Read a complete result set despite the PostgREST per-request row cap."""
    rows = []
    for page in range(max_pages):
        start = page * page_size
        batch = _exec_query_get_data(query.range(start, start + page_size - 1))
        rows.extend(batch)
        if len(batch) < page_size:
            return rows
    raise HTTPException(status_code=503, detail="Database result exceeds the configured pagination limit")


def _update_record(table_name: str, record_id: UUID | str, payload: dict) -> dict | None:
    """Standard admin update helper for a single record.

    Returns the updated row or None when no matching row exists.
    """
    if not payload:
        return None
    sb = get_supabase()
    result = sb.table(table_name).update(payload).eq("id", str(record_id)).execute()
    return result.data[0] if result.data else None


def _delete_record(table_name: str, record_id: UUID | str) -> dict | None:
    """Standard admin delete helper for a single record."""
    sb = get_supabase()
    result = sb.table(table_name).delete().eq("id", str(record_id)).execute()
    if not result.data:
        return None
    deleted = result.data[0].copy()
    deleted["deleted"] = True
    return deleted


# ---------- zones ----------

def list_zones(district: str | None = None) -> list[dict]:
    sb = get_supabase()
    query = sb.table("zones").select("*")
    if district:
        query = query.eq("district", district)
    return _exec_query_get_all(query.order("id"))


def create_zone(zone: dict) -> dict:
    sb = get_supabase()
    result = sb.table("zones").insert(zone).execute()
    return result.data[0]


def get_zone(zone_id: UUID) -> dict | None:
    sb = get_supabase()
    result = sb.table("zones").select("*").eq("id", str(zone_id)).execute()
    return result.data[0] if result.data else None


def update_zone(zone_id: UUID | str, payload: dict) -> dict | None:
    return _update_record("zones", zone_id, payload)


def delete_zone(zone_id: UUID | str) -> dict | None:
    return _delete_record("zones", zone_id)


def get_zone_by_district(district: str) -> list[dict]:
    """Backward-compatible helper: return zones matching a district name.

    Some callers expect a function named `get_zone_by_district`; implement
    as a thin wrapper around `list_zones` to avoid duplication.
    """
    return list_zones(district=district)


# ---------- agri_metrics ----------

def list_agri_metrics(zone_id: UUID | None = None, season: str | None = None,
                       crop: str | None = None, district: str | None = None) -> list[dict]:
    """Browse agri_metrics, optionally joined to the zone's district for filtering
    without a separate zone lookup (used by /segmentation/agri-metrics)."""
    sb = get_supabase()
    query = sb.table("agri_metrics").select("*, zones(district, sector, cell)")
    if zone_id:
        query = query.eq("zone_id", str(zone_id))
    if season:
        query = query.eq("season", season)
    if crop:
        query = query.eq("crop", crop)
    rows = _exec_query_get_all(query.order("id"))
    if district:
        rows = [r for r in rows if (r.get("zones") or {}).get("district") == district]
    return rows


def list_district_agri_metrics(district: str, season: str | None = None) -> list[dict]:
    """Fetch crop evidence only for zones in one district, with optional season filtering."""
    zones = list_zones(district=district)
    zone_ids = [str(zone["id"]) for zone in zones if zone.get("id")]
    if not zone_ids:
        return []
    query = (
        get_supabase().table("agri_metrics")
        .select("crop,season,yield_actual,production_mt,area_cultivated,rainfall_mm,soil_type,household_size,zone_id")
        .in_("zone_id", zone_ids)
    )
    if season:
        query = query.eq("season", season)
    return _exec_query_get_all(query.order("season").order("crop"))


def list_district_alerts(district: str) -> list[dict]:
    """Return alerts for zones in one district without mixing other districts."""
    zones = list_zones(district=district)
    zone_ids = [str(zone["id"]) for zone in zones if zone.get("id")]
    if not zone_ids:
        return []
    query = get_supabase().table("alerts").select("*").in_("zone_id", zone_ids)
    return _exec_query_get_all(query.order("created_at", desc=True).order("id"))


def create_agri_metric(metric: dict) -> dict:
    sb = get_supabase()
    result = sb.table("agri_metrics").insert(metric).execute()
    return result.data[0]


def update_agri_metric(metric_id: UUID | str, payload: dict) -> dict | None:
    return _update_record("agri_metrics", metric_id, payload)


def delete_agri_metric(metric_id: UUID | str) -> dict | None:
    return _delete_record("agri_metrics", metric_id)


def upsert_agri_metric(metric: dict) -> dict:
    """Insert-or-update on (zone_id, season, crop) - what the seeding script uses
    so re-running it never creates duplicate rows."""
    sb = get_supabase()
    result = (
        sb.table("agri_metrics")
        .upsert(metric, on_conflict="zone_id,season,crop")
        .execute()
    )
    return result.data[0]


def crop_comparison(district: str, season: str | None = None) -> list[dict]:
    """All crops grown in a district (optionally one season), sorted by yield -
    powers the 'what should this zone grow' view."""
    rows = list_district_agri_metrics(district, season)
    return sorted(rows, key=lambda r: r.get("yield_actual") or 0, reverse=True)


# ---------- predictions ----------

_PREDICTION_INSERT_COLUMNS = {
    "id",
    "zone_id",
    "season",
    "crop",
    "predicted_yield",
    "priority_level",
    "confidence",
    "model_version",
    "created_at",
}


def save_prediction(prediction: dict) -> dict:
    sb = get_supabase()
    payload = {key: value for key, value in prediction.items() if key in _PREDICTION_INSERT_COLUMNS}
    result = sb.table("predictions").insert(payload).execute()
    return result.data[0]


def update_prediction(prediction_id: UUID | str, payload: dict) -> dict | None:
    return _update_record("predictions", prediction_id, payload)


def delete_prediction(prediction_id: UUID | str) -> dict | None:
    return _delete_record("predictions", prediction_id)


def list_predictions(zone_id: UUID | None = None) -> list[dict]:
    sb = get_supabase()
    query = sb.table("predictions").select("*")
    if zone_id:
        query = query.eq("zone_id", str(zone_id))
    return _exec_query_get_all(query.order("created_at", desc=True).order("id"))


def priority_ranking(season: str | None = None) -> list[dict]:
    """All predictions, most recent per zone, sorted High -> Low priority."""
    sb = get_supabase()
    query = sb.table("predictions").select("*, zones(district, sector, cell)")
    if season:
        query = query.eq("season", season)
    rows = _exec_query_get_all(query.order("created_at", desc=True).order("id"))
    latest_by_zone = {}
    for row in rows:
        latest_by_zone.setdefault(str(row.get("zone_id")), row)
    rows = list(latest_by_zone.values())
    order = {"High": 0, "Medium": 1, "Low": 2}
    return sorted(rows, key=lambda r: order.get(r.get("priority_level"), 3))


# ---------- alignment_metrics ----------

def upsert_alignment_metric(metric: dict) -> dict:
    """Insert-or-update on (zone_id, season) so repeated alignment runs remain idempotent."""
    sb = get_supabase()
    result = (
        sb.table("alignment_metrics")
        .upsert(metric, on_conflict="zone_id,season")
        .execute()
    )
    return result.data[0]


def update_alignment_metric(metric_id: UUID | str, payload: dict) -> dict | None:
    return _update_record("alignment_metrics", metric_id, payload)


def delete_alignment_metric(metric_id: UUID | str) -> dict | None:
    return _delete_record("alignment_metrics", metric_id)


def get_alignment_metric(zone_id: UUID) -> dict | None:
    sb = get_supabase()
    result = (
        sb.table("alignment_metrics")
        .select("*")
        .eq("zone_id", str(zone_id))
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def list_alignment_metrics() -> list[dict]:
    sb = get_supabase()
    return _exec_query_get_all(sb.table("alignment_metrics").select("*").order("id"))


def get_zone_readiness(zone_id: UUID | str) -> dict | None:
    result = get_supabase().table("zone_readiness").select("*").eq("zone_id", str(zone_id)).limit(1).execute()
    return result.data[0] if result.data else None


def upsert_zone_readiness(zone_id: UUID | str, finance_evidence: dict, export_evidence: dict) -> dict:
    payload = {"zone_id": str(zone_id), "finance_evidence": finance_evidence,
               "export_evidence": export_evidence}
    result = get_supabase().table("zone_readiness").upsert(payload, on_conflict="zone_id").execute()
    return result.data[0]


def create_zone_work_record(record: dict) -> dict:
    result = get_supabase().table("zone_work_records").insert(record).execute()
    return result.data[0]


def list_zone_work_records(zone_id: UUID | str | None = None, limit: int = 100) -> list[dict]:
    query = get_supabase().table("zone_work_records").select("*")
    if zone_id:
        query = query.eq("zone_id", str(zone_id))
    return _exec_query_get_all(query.order("recorded_at", desc=True).limit(max(1, min(int(limit), 500))))


# ---------- plans ----------

def create_plan(plan: dict) -> dict:
    sb = get_supabase()
    result = sb.table("plans").insert(plan).execute()
    return result.data[0]


def update_plan(plan_id: UUID | str, payload: dict) -> dict | None:
    return _update_record("plans", plan_id, payload)


def delete_plan(plan_id: UUID | str) -> dict | None:
    return _delete_record("plans", plan_id)


def list_plans(zone_id: UUID | None = None) -> list[dict]:
    sb = get_supabase()
    query = sb.table("plans").select("*")
    if zone_id:
        query = query.eq("zone_id", str(zone_id))
    return _exec_query_get_all(query.order("created_at", desc=True).order("id"))


def get_plan(plan_id: UUID | str) -> dict | None:
    sb = get_supabase()
    rows = _exec_query_get_data(sb.table("plans").select("*").eq("id", str(plan_id)).limit(1))
    return rows[0] if rows else None


# ---------- alerts ----------

def create_alert(alert: dict) -> dict:
    sb = get_supabase()
    result = sb.table("alerts").insert(alert).execute()
    return result.data[0]


def get_alert(alert_id: UUID | str) -> dict | None:
    rows = _exec_query_get_data(
        get_supabase().table("alerts").select("*").eq("id", str(alert_id)).limit(1)
    )
    return rows[0] if rows else None


def get_alert_contact_delivery(alert_id: UUID | str, contact_id: UUID | str) -> dict | None:
    rows = _exec_query_get_data(
        get_supabase().table("message_log").select("*")
        .eq("alert_id", str(alert_id)).eq("contact_id", str(contact_id))
        .eq("direction", "outbound").limit(1)
    )
    return rows[0] if rows else None


def list_alert_deliveries(alert_id: UUID | str) -> list[dict]:
    return _exec_query_get_data(
        get_supabase().table("message_log").select("status,error_code")
        .eq("alert_id", str(alert_id)).eq("direction", "outbound")
    )


def count_outbound_messages_since(contact_id: UUID | str, since: str) -> int:
    rows = _exec_query_get_data(
        get_supabase().table("message_log").select("id")
        .eq("contact_id", str(contact_id)).eq("direction", "outbound")
        .gte("created_at", since)
    )
    return len(rows)


def count_alert_subscription_contacts(zone_id: UUID | str, crop: str | None, severity: str) -> int:
    severity_order = {"info": 0, "warning": 1, "critical": 2}
    required = severity_order.get(str(severity).lower())
    if required is None:
        return 0
    subscriptions = _exec_query_get_data(
        get_supabase().table("alert_subscriptions").select("contact_id,zone_id,crop,min_severity")
    )
    matching_ids = {
        str(item["contact_id"])
        for item in subscriptions
        if (item.get("zone_id") is None or str(item.get("zone_id")) == str(zone_id))
        and (item.get("crop") is None or item.get("crop") == crop)
        and severity_order.get(str(item.get("min_severity", "warning")).lower(), 3) <= required
    }
    if not matching_ids:
        return 0
    rows = _exec_query_get_data(
        get_supabase().table("contacts").select("id").in_("id", list(matching_ids)).is_("deleted_at", "null")
    )
    return len(rows)


def get_whatsapp_template(name: str, language: str) -> dict | None:
    rows = _exec_query_get_data(
        get_supabase().table("whatsapp_templates").select("*")
        .eq("name", name).eq("language", language).limit(1)
    )
    return rows[0] if rows else None


def list_whatsapp_templates() -> list[dict]:
    return _exec_query_get_data(
        get_supabase().table("whatsapp_templates").select("*").order("name").order("language")
    )


def upsert_whatsapp_template(template: dict) -> dict:
    result = get_supabase().table("whatsapp_templates").upsert(
        template, on_conflict="name,language"
    ).execute()
    return result.data[0]


def set_whatsapp_template_status(name: str, language: str, status: str) -> dict | None:
    result = get_supabase().table("whatsapp_templates").update({"status": status})
    result = result.eq("name", name).eq("language", language).execute()
    return result.data[0] if result.data else None


def whatsapp_health_counts(since: str) -> dict:
    templates = _exec_query_get_data(
        get_supabase().table("whatsapp_templates").select("name").eq("status", "approved")
    )
    last_events = _exec_query_get_data(
        get_supabase().table("webhook_events").select("received_at")
        .order("received_at", desc=True).limit(1)
    )
    failed = _exec_query_get_data(
        get_supabase().table("message_log").select("id").eq("status", "failed").gte("created_at", since)
    )
    return {
        "approved_templates": len(templates),
        "last_webhook_received_at": last_events[0].get("received_at") if last_events else None,
        "failed_messages_24h": len(failed),
    }


def whatsapp_stats_rows(since: str) -> list[dict]:
    return _exec_query_get_data(
        get_supabase().table("message_log").select("status,kind,error_code").gte("created_at", since)
    )


def update_alert(alert_id: UUID | str, payload: dict) -> dict | None:
    return _update_record("alerts", alert_id, payload)


def delete_alert(alert_id: UUID | str) -> dict | None:
    return _delete_record("alerts", alert_id)


def delete_all_alerts() -> None:
    sb = get_supabase()
    # UUID primary keys are non-null; excluding the nil UUID gives PostgREST a
    # safe filter while matching every real alert row.
    sb.table("alerts").delete().neq("id", str(UUID(int=0))).execute()


def list_alerts(zone_id: UUID | None = None) -> list[dict]:
    sb = get_supabase()
    query = sb.table("alerts").select("*")
    if zone_id:
        query = query.eq("zone_id", str(zone_id))
    return _exec_query_get_all(query.order("created_at", desc=True).order("id"))


# ---------- field reports ----------

def create_field_report(report: dict) -> dict:
    sb = get_supabase()
    result = sb.table("field_reports").insert(report).execute()
    return result.data[0]


def list_field_reports(zone_id: UUID, limit: int = 20) -> list[dict]:
    sb = get_supabase()
    query = (sb.table("field_reports").select("*").eq("zone_id", str(zone_id))
             .order("submitted_at", desc=True).limit(max(1, min(int(limit), 100))))
    return _exec_query_get_data(query)
