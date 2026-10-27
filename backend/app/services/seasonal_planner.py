from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import logging
import re
import threading
import time
import unicodedata
from typing import Any

import httpx

from app.db.rwanda_districts import RWANDA_DISTRICTS
from app.ml.predict import get_district_evidence_ranking, known_crops
from app.services.weather_service import fetch_weather

logger = logging.getLogger(__name__)

FAO_API_BASE = "https://api-cropcalendar.apps.fao.org/api/v1"
FAO_CROP_CALENDAR_URL = "https://cropcalendar.apps.fao.org/"
FAO_CALENDAR_CACHE_SECONDS = 6 * 60 * 60
_FAO_CACHE: tuple[float, dict[str, Any]] | None = None
_FAO_CACHE_LOCK = threading.Lock()

# These are crop-name equivalents only; all calendar dates and rates come from FAO.
_CROP_EQUIVALENTS = {
    "maize": "corn",
    "beans": "bean",
    "bush bean": "bean",
    "climbing bean": "bean",
    "groundnut": "peanut",
    "irish potato": "potato",
    "paddy rice": "rice",
    "wheat": "wheat bread",
    "pea": "pea dry",
    "cooking banana": "banana",
    "dessert banana": "banana",
}


class CropCalendarUnavailable(RuntimeError):
    """FAO crop-calendar data could not be loaded."""


def _normalize(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(character for character in text if not unicodedata.combining(character))
    return " ".join(re.findall(r"[a-z0-9]+", text.casefold()))


def _request_list(path: str) -> list[dict[str, Any]]:
    response = httpx.get(
        f"{FAO_API_BASE}{path}",
        params={"language": "en"},
        timeout=15.0,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list) or any(not isinstance(item, dict) for item in payload):
        raise CropCalendarUnavailable(f"FAO returned an invalid response for {path}")
    return payload


def _load_fao_data() -> tuple[dict[str, Any], bool]:
    global _FAO_CACHE
    now = time.monotonic()
    if _FAO_CACHE and now - _FAO_CACHE[0] < FAO_CALENDAR_CACHE_SECONDS:
        return _FAO_CACHE[1], False

    with _FAO_CACHE_LOCK:
        now = time.monotonic()
        if _FAO_CACHE and now - _FAO_CACHE[0] < FAO_CALENDAR_CACHE_SECONDS:
            return _FAO_CACHE[1], False
        try:
            data = {
                "zones": _request_list("/countries/RW/aez"),
                "crops": _request_list("/countries/RW/crops"),
                "calendar": _request_list("/countries/RW/cropCalendar"),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
        except (httpx.HTTPError, ValueError, CropCalendarUnavailable) as exc:
            if _FAO_CACHE:
                logger.warning("FAO crop calendar refresh failed; serving cached data: %s", exc)
                return _FAO_CACHE[1], True
            logger.exception("FAO crop calendar could not be loaded")
            raise CropCalendarUnavailable("The FAO Crop Calendar is temporarily unavailable.") from exc
        _FAO_CACHE = (time.monotonic(), data)
        return data, False


def _district_zones(district: str, zones: list[dict[str, Any]]) -> list[dict[str, Any]]:
    district_name = next(
        (item["district"] for item in RWANDA_DISTRICTS
         if _normalize(item["district"]) == _normalize(district)),
        None,
    )
    if not district_name:
        return []
    pattern = re.compile(rf"(?<![a-z]){re.escape(_normalize(district_name))}(?![a-z])")
    return [
        zone for zone in zones
        if pattern.search(_normalize(zone.get("administratrative_units")))
    ]


def _crop_identifiers(crop: str, crops: list[dict[str, Any]]) -> set[str]:
    name = _normalize(crop)
    canonical = _CROP_EQUIVALENTS.get(name, name)
    identifiers: set[str] = set()
    for item in crops:
        labels = {
            _normalize(item.get("crop_name")),
            _normalize(item.get("other_name")),
        }
        if canonical in labels or name in labels:
            crop_id = str(item.get("crop_id") or "").strip()
            if crop_id:
                identifiers.add(crop_id)
    return identifiers


def _calendar_crop_ids(calendar_crop: dict[str, Any]) -> set[str]:
    result = set()
    for crop in (calendar_crop, calendar_crop.get("cropParent") or {}):
        value = str(crop.get("id") or "").strip()
        if value:
            result.add(value)
    return result


def _calendar_crop_name(crop: str, calendar: list[dict[str, Any]]) -> str | None:
    name = _normalize(crop)
    canonical = _CROP_EQUIVALENTS.get(name, name)
    for row in calendar:
        item = row.get("crop") or {}
        if canonical in {
            _normalize(item.get("name")),
            _normalize((item.get("cropParent") or {}).get("name")),
        }:
            return str(item.get("name") or (item.get("cropParent") or {}).get("name"))
    return None


def _date_in_year(value: object, year: int) -> date | None:
    if not isinstance(value, dict):
        return None
    try:
        return date(year, int(value["month"]), int(value["day"]))
    except (KeyError, TypeError, ValueError):
        return None


def _upcoming_window(
    session: dict[str, Any],
    start_key: str,
    end_key: str,
    today: date,
) -> tuple[date, date] | None:
    for year in range(today.year - 1, today.year + 4):
        start = _date_in_year(session.get(start_key), year)
        end = _date_in_year(session.get(end_key), year)
        if start is None or end is None:
            continue
        if end < start:
            end = end.replace(year=end.year + 1)
        if end >= today:
            return start, end
    return None


def _growing_period_days(value: object) -> int | None:
    if not isinstance(value, dict):
        return None
    numbers = [float(item) for item in re.findall(r"\d+(?:\.\d+)?", str(value.get("value") or ""))]
    if not numbers:
        return None
    days = sum(numbers) / len(numbers)
    period = _normalize(value.get("period"))
    if "month" in period:
        days *= 30
    elif "year" in period:
        days *= 365
    return max(1, round(days))


def _seed_rate(session: dict[str, Any], area_ha: float | None) -> dict[str, Any] | None:
    rate = session.get("sowing_rate")
    if not isinstance(rate, dict):
        return None
    unit = str(rate.get("unit") or "").strip()
    values = [float(item) for item in re.findall(r"\d+(?:[.,]\d+)?", str(rate.get("value") or ""))]
    if not unit or not values:
        return None
    lower = min(values)
    upper = max(values)
    result: dict[str, Any] = {"rate_min": lower, "rate_max": upper, "unit": unit}
    if area_ha is not None and area_ha > 0 and _normalize(unit) in {"kg ha", "kg hectare"}:
        result["quantity_min"] = round(lower * area_ha, 2)
        result["quantity_max"] = round(upper * area_ha, 2)
        result["area_ha"] = area_ha
    return result


def _format_date_range(start: date, end: date) -> str:
    if start.year == end.year:
        return f"{start:%d %b}–{end:%d %b %Y}"
    return f"{start:%d %b %Y}–{end:%d %b %Y}"


def _nisr_evidence(crop: str, district: str) -> dict[str, Any]:
    sources = known_crops()
    normalized = _normalize(crop)
    canonical = _CROP_EQUIVALENTS.get(normalized, normalized)
    evidence_crop = next(
        (
            item for item in sources
            if _normalize(item) == normalized
            or _CROP_EQUIVALENTS.get(_normalize(item), _normalize(item)) == canonical
        ),
        None,
    )
    if not evidence_crop:
        return {"status": "unavailable", "reason": "No matching NISR crop record was found."}
    try:
        evidence = get_district_evidence_ranking(evidence_crop)
    except Exception:
        logger.exception("NISR planning evidence unavailable for %s", evidence_crop)
        return {"status": "unavailable", "reason": "NISR comparison could not be loaded."}

    row = next(
        (item for item in evidence.get("rows", [])
         if _normalize(item.get("district")) == _normalize(district)),
        None,
    )
    if not row:
        return {
            "status": "unavailable",
            "crop": evidence_crop,
            "reason": "No district-level NISR yield record was found for this crop.",
            "source": "NISR records and official NISR SAS history",
        }
    return {
        "status": "available",
        "crop": evidence_crop,
        "district_yield_kg_ha": row.get("yield_kg_ha"),
        "national_reference_kg_ha": evidence.get("national_reference_kg_ha"),
        "district_rank": row.get("rank"),
        "districts_with_evidence": evidence.get("districts_with_evidence"),
        "observation_count": row.get("observation_count"),
        "seasons": row.get("seasons") or [],
        "trend_change_pct": row.get("trend_change_pct"),
        "trend_season_code": row.get("trend_season_code"),
        "sources": row.get("sources") or [],
        "interpretation": evidence.get("interpretation"),
    }


def build_seasonal_draft(
    district: str,
    crop: str,
    area_ha: float | None = None,
    today: date | None = None,
) -> dict[str, Any]:
    """Build an editable seasonal draft from FAO calendar and NISR evidence."""
    target_date = today or date.today()
    data, stale = _load_fao_data()
    zones = _district_zones(district, data["zones"])
    if not zones:
        return {
            "status": "calendar_unavailable_for_district",
            "message": "FAO has not mapped this district to a crop-calendar agro-ecological zone.",
            "district": district,
            "roadmap": [],
            "sources": [{"name": "FAO Crop Calendar", "url": FAO_CROP_CALENDAR_URL}],
        }

    crop_ids = _crop_identifiers(crop, data["crops"])
    calendar_crop = _calendar_crop_name(crop, data["calendar"])
    if not crop_ids or not calendar_crop:
        normalized_crop = _normalize(crop)
        message = f"No Rwanda crop-calendar schedule is available for {crop}."
        sources = [{"name": "FAO Crop Calendar", "url": FAO_CROP_CALENDAR_URL}]
        if normalized_crop in {"banana", "cooking banana", "dessert banana"}:
            message = (
                "FAO does not currently publish a Rwanda seasonal schedule for banana. "
                "Banana tasks depend on planting date and local field conditions, so no Season A/B dates are inferred. "
                "Create a manual plan and consult the Rwanda banana extension reference for task guidance."
            )
            sources.append({
                "name": "Rwanda banana extension guidance (eHinga)",
                "url": "https://ehinga.org/en_bananas/",
            })
        return {
            "status": "calendar_unavailable_for_crop",
            "message": message,
            "district": district,
            "crop": crop,
            "roadmap": [],
            "sources": sources,
        }

    zone_ids = {str(zone.get("zone_id")) for zone in zones}
    candidates = [
        (row, session)
        for row in data["calendar"]
        if str(row.get("aez", {}).get("id")) in zone_ids
        and _calendar_crop_ids(row.get("crop") or {}) & crop_ids
        for session in row.get("sessions") or []
    ]
    windows = []
    for row, session in candidates:
        window = _upcoming_window(session, "early_sowing", "later_sowing", target_date)
        if window:
            windows.append((window[0], window[1], row, session))
    if not windows:
        return {
            "status": "calendar_schedule_unavailable",
            "message": f"The FAO calendar has no upcoming sowing window for {crop} in {district}.",
            "district": district,
            "crop": crop,
            "roadmap": [],
            "sources": [{"name": "FAO Crop Calendar", "url": FAO_CROP_CALENDAR_URL}],
        }

    sowing_start, sowing_end, calendar_row, session = min(windows, key=lambda item: item[0])
    sowing_due = max(target_date, sowing_start)
    harvest_window = _upcoming_window(
        session, "early_harvest", "late_harvest", sowing_due,
    )
    if harvest_window and harvest_window[0] < sowing_due:
        harvest_window = _upcoming_window(
            session, "early_harvest", "late_harvest", sowing_due + timedelta(days=1),
        )
    growing_days = _growing_period_days(session.get("growing_period"))
    seed_rate = _seed_rate(session, area_ha)
    aez_name = str((calendar_row.get("aez") or {}).get("name") or "")
    published_crop = str((calendar_row.get("crop") or {}).get("name") or calendar_crop)
    last_updated = str(calendar_row.get("lastUpdated") or "")
    try:
        source_age_days = (target_date - datetime.strptime(last_updated, "%d/%m/%Y").date()).days
    except ValueError:
        source_age_days = None
    source_is_old = source_age_days is not None and source_age_days > 365
    sowing_dates = _format_date_range(sowing_start, sowing_end)
    yield_evidence = _nisr_evidence(crop, district)
    seed_rate_text = ""
    if seed_rate:
        seed_rate_text = (
            f" FAO lists a sowing-rate range of {seed_rate['rate_min']:g}–"
            f"{seed_rate['rate_max']:g} {seed_rate['unit']}."
        )
    roadmap = [
        {
            "step_number": 1,
            "title": f"Prepare for {crop} sowing",
            "description": (
                f"The FAO Crop Calendar places the sowing window at {sowing_dates} "
                f"for {aez_name}. Arrange seed and field access before the window."
                f"{seed_rate_text}"
            ),
            "timeframe": f"Before {sowing_dates}",
            "due_date": max(target_date, sowing_start - timedelta(days=14)).isoformat(),
            "status": "planned",
        },
        {
            "step_number": 2,
            "title": f"Plant {crop} within its local calendar window",
            "description": (
                f"The Rwanda FAO Crop Calendar lists {sowing_dates} for "
                f"{published_crop} in {aez_name}. This is regional guidance; "
                "record the actual planting date and area for this farm."
                f"{seed_rate_text}"
            ),
            "timeframe": sowing_dates,
            "due_date": sowing_due.isoformat(),
            "status": "planned",
        },
    ]
    monitor_date = None
    if growing_days:
        monitor_date = sowing_due + timedelta(days=max(1, growing_days // 2))
        if harvest_window:
            latest_monitor_date = harvest_window[0] - timedelta(days=7)
            if latest_monitor_date > sowing_due:
                monitor_date = min(monitor_date, latest_monitor_date)
        description = (
            f"Record crop condition, planted area, and field issues around the "
            f"midpoint of the FAO-listed {session.get('growing_period', {}).get('value')} "
            f"{session.get('growing_period', {}).get('period', 'growing period')}. "
            "Use the farm's own observations to decide what needs attention."
        )
        roadmap.append({
            "step_number": len(roadmap) + 1,
            "title": f"Check {crop} field progress",
            "description": description,
            "timeframe": f"Around {monitor_date:%d %b %Y}",
            "due_date": monitor_date.isoformat(),
            "status": "planned",
        })
    if harvest_window:
        harvest_start, harvest_end = harvest_window
        roadmap.append({
            "step_number": len(roadmap) + 1,
            "title": f"Prepare for {crop} harvest",
            "description": (
                f"The FAO Crop Calendar lists a harvest window of "
                f"{_format_date_range(harvest_start, harvest_end)} for {aez_name}. "
                "Arrange labour, storage, and transport, and record the farm's harvested "
                "area and production."
            ),
            "timeframe": _format_date_range(harvest_start, harvest_end),
            "due_date": harvest_start.isoformat(),
            "status": "planned",
        })

    weather = fetch_weather(district=district)
    return {
        "status": "ready",
        "title": f"{crop} seasonal plan · {district}",
        "district": district,
        "crop": crop,
        "season": f"FAO sowing window {sowing_start.year}",
        "area_ha": area_ha,
        "calendar": {
            "source": "FAO Crop Calendar",
            "source_url": FAO_CROP_CALENDAR_URL,
            "last_updated": last_updated,
            "source_age_days": source_age_days,
            "source_is_old": source_is_old,
            "fetched_at": data["fetched_at"],
            "stale": stale,
            "aez": aez_name,
            "crop": published_crop,
            "sowing_start": sowing_start.isoformat(),
            "sowing_end": sowing_end.isoformat(),
            "harvest_start": harvest_window[0].isoformat() if harvest_window else None,
            "harvest_end": harvest_window[1].isoformat() if harvest_window else None,
            "growing_period": session.get("growing_period"),
            "sowing_rate": seed_rate,
        },
        "nisr_evidence": yield_evidence,
        "weather": weather,
        "sources": [
            {"name": "FAO Crop Calendar", "url": FAO_CROP_CALENDAR_URL, "last_updated": last_updated},
            {"name": "NISR official yield observations", "scope": "district and crop historical comparison"},
            {"name": "Open-Meteo", "scope": "short-range district weather forecast"},
        ],
        "roadmap": roadmap,
        "planning_note": (
            "Dates and sowing rates are FAO agro-ecological-zone guidance, not a farm-specific guarantee. "
            "NISR yield evidence is historical district context, not a farm forecast. "
            "Weather is a short-range forecast and does not change the FAO seasonal calendar."
            + (" The FAO calendar record is more than a year old; verify the season dates locally."
               if source_is_old else "")
        ),
    }
