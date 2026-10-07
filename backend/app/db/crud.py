"""
All direct Supabase table access lives here. Routers and services call
these functions rather than touching the Supabase client directly -
keeps query logic in one place if the schema changes.
"""
from uuid import UUID
import logging
import time
from fastapi import HTTPException
import httpx
from postgrest import exceptions as postgrest_exceptions
from app.core.supabase_client import get_supabase


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
            raise HTTPException(status_code=503, detail=f"Supabase API error: {getattr(e, 'message', str(e))}")
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
    zones = list_zones(district=district)
    if not zones:
        return []
    zone_ids = {z["id"] for z in zones}
    metrics = list_agri_metrics(season=season)
    rows = [m for m in metrics if m.get("zone_id") in zone_ids]
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


# ---------- alerts ----------

def create_alert(alert: dict) -> dict:
    sb = get_supabase()
    result = sb.table("alerts").insert(alert).execute()
    return result.data[0]


def update_alert(alert_id: UUID | str, payload: dict) -> dict | None:
    return _update_record("alerts", alert_id, payload)


def delete_alert(alert_id: UUID | str) -> dict | None:
    return _delete_record("alerts", alert_id)


def list_alerts(zone_id: UUID | None = None) -> list[dict]:
    sb = get_supabase()
    query = sb.table("alerts").select("*")
    if zone_id:
        query = query.eq("zone_id", str(zone_id))
    return _exec_query_get_all(query.order("created_at", desc=True).order("id"))
