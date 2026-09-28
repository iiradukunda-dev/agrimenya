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


# ---------- zones ----------

def list_zones(district: str | None = None) -> list[dict]:
    sb = get_supabase()
    query = sb.table("zones").select("*")
    if district:
        query = query.eq("district", district)
    return _exec_query_get_data(query)


def create_zone(zone: dict) -> dict:
    sb = get_supabase()
    result = sb.table("zones").insert(zone).execute()
    return result.data[0]


def get_zone(zone_id: UUID) -> dict | None:
    sb = get_supabase()
    result = sb.table("zones").select("*").eq("id", str(zone_id)).execute()
    return result.data[0] if result.data else None


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
    rows = _exec_query_get_data(query)
    if district:
        rows = [r for r in rows if (r.get("zones") or {}).get("district") == district]
    return rows


def create_agri_metric(metric: dict) -> dict:
    sb = get_supabase()
    result = sb.table("agri_metrics").insert(metric).execute()
    return result.data[0]


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
    rows = [m for m in metrics if m["zone_id"] in zone_ids]
    return sorted(rows, key=lambda r: r.get("yield_actual") or 0, reverse=True)


# ---------- predictions ----------

def save_prediction(prediction: dict) -> dict:
    sb = get_supabase()
    result = sb.table("predictions").insert(prediction).execute()
    return result.data[0]


def list_predictions(zone_id: UUID | None = None) -> list[dict]:
    sb = get_supabase()
    query = sb.table("predictions").select("*")
    if zone_id:
        query = query.eq("zone_id", str(zone_id))
    return _exec_query_get_data(query.order("created_at", desc=True))


def priority_ranking(season: str | None = None) -> list[dict]:
    """All predictions, most recent per zone, sorted High -> Low priority."""
    sb = get_supabase()
    query = sb.table("predictions").select("*, zones(district, sector, cell)")
    if season:
        query = query.eq("season", season)
    rows = _exec_query_get_data(query)
    order = {"High": 0, "Medium": 1, "Low": 2}
    return sorted(rows, key=lambda r: order.get(r.get("priority_level"), 3))


# ---------- alignment_metrics ----------

def upsert_alignment_metric(metric: dict) -> dict:
    sb = get_supabase()
    result = sb.table("alignment_metrics").insert(metric).execute()
    return result.data[0]


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
    return _exec_query_get_data(sb.table("alignment_metrics").select("*"))


# ---------- plans ----------

def create_plan(plan: dict) -> dict:
    sb = get_supabase()
    result = sb.table("plans").insert(plan).execute()
    return result.data[0]


def list_plans(zone_id: UUID | None = None) -> list[dict]:
    sb = get_supabase()
    query = sb.table("plans").select("*")
    if zone_id:
        query = query.eq("zone_id", str(zone_id))
    return _exec_query_get_data(query)


# ---------- alerts ----------

def create_alert(alert: dict) -> dict:
    sb = get_supabase()
    result = sb.table("alerts").insert(alert).execute()
    return result.data[0]


def list_alerts(zone_id: UUID | None = None) -> list[dict]:
    sb = get_supabase()
    query = sb.table("alerts").select("*")
    if zone_id:
        query = query.eq("zone_id", str(zone_id))
    return _exec_query_get_data(query.order("created_at", desc=True))
