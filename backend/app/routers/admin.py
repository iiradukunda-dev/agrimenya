from typing import Any
from uuid import UUID
import math
import csv
import hashlib
import io
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from app.core.auth import require_role
from app.core.audit import audit_admin_action
from app.core.config import settings
from app.db import crud
from app.db.rwanda_districts import RWANDA_DISTRICTS

router = APIRouter(prefix="/admin", tags=["Admin"])
logger = logging.getLogger(__name__)
_SEASON_PATTERN = re.compile(r"^20\d{2}\s+Season\s+[ABC]$", re.IGNORECASE)

_PATCH_FIELDS = {
    "zones": {"district", "sector", "cell", "latitude", "longitude", "crop_type", "season"},
    "plans": {"title", "roadmap_json", "resources_json", "created_by"},
    "alerts": {"message", "severity", "created_by", "zone_id", "crop", "action", "allow_links"},
}


def _check_patch(resource: str, payload: dict[str, Any]) -> None:
    if not payload or set(payload) - _PATCH_FIELDS[resource]:
        raise HTTPException(status_code=422, detail="Patch contains no fields or unsupported fields")


@router.get("/zones")
def list_admin_zones(district: str | None = None, _: dict = Depends(require_role("admin"))):
    audit_admin_action("list_zones", "zones", {"district": district})
    return crud.list_zones(district=district)


@router.patch("/zones/{zone_id}")
def update_admin_zone(zone_id: UUID, payload: dict[str, Any], request: Request, _: dict = Depends(require_role("admin"))):
    _check_patch("zones", payload)
    for key, low, high in (("latitude", -90, 90), ("longitude", -180, 180)):
        if key in payload:
            value = payload[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
                raise HTTPException(status_code=422, detail=f"{key} is outside valid bounds")
    zone = crud.get_zone(zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    updated = crud.update_zone(zone_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Zone update failed")
    audit_admin_action("update_zone", "zones", {"zone_id": zone_id, "changes": payload}, request=request)
    return updated


@router.delete("/zones/{zone_id}")
def delete_admin_zone(zone_id: UUID, request: Request, _: dict = Depends(require_role("admin"))):
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
def update_admin_plan(plan_id: UUID, payload: dict[str, Any], request: Request, _: dict = Depends(require_role("admin"))):
    _check_patch("plans", payload)
    plan = crud.list_plans()
    if not any(str(item.get("id")) == str(plan_id) for item in plan):
        raise HTTPException(status_code=404, detail="Plan not found")
    updated = crud.update_plan(plan_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Plan update failed")
    audit_admin_action("update_plan", "plans", {"plan_id": plan_id, "changes": payload}, request=request)
    return updated


@router.delete("/plans/{plan_id}")
def delete_admin_plan(plan_id: UUID, request: Request, _: dict = Depends(require_role("admin"))):
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
def update_admin_alert(alert_id: UUID, payload: dict[str, Any], request: Request, _: dict = Depends(require_role("admin"))):
    _check_patch("alerts", payload)
    if payload.get("severity") not in {None, "Info", "Warning", "Critical"}:
        raise HTTPException(status_code=422, detail="Invalid alert severity")
    if "allow_links" in payload and not isinstance(payload["allow_links"], bool):
        raise HTTPException(status_code=422, detail="allow_links must be a boolean")
    alerts = crud.list_alerts()
    if not any(str(item.get("id")) == str(alert_id) for item in alerts):
        raise HTTPException(status_code=404, detail="Alert not found")
    update_payload = dict(payload)
    update_payload.update({"status": "draft", "approved_by": None, "approved_at": None})
    updated = crud.update_alert(alert_id, update_payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Alert update failed")
    audit_admin_action("update_alert", "alerts", {"alert_id": str(alert_id), "changed_fields": sorted(payload)}, request=request)
    return updated


@router.delete("/alerts/{alert_id}")
def delete_admin_alert(alert_id: UUID, request: Request, _: dict = Depends(require_role("admin"))):
    deleted = crud.delete_alert(alert_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Alert not found")
    audit_admin_action("delete_alert", "alerts", {"alert_id": alert_id}, request=request)
    return deleted


@router.delete("/alerts")
def clear_admin_alerts(request: Request, _: dict = Depends(require_role("admin"))):
    crud.delete_all_alerts()
    audit_admin_action("clear_alerts", "alerts", {}, request=request)
    return {"cleared": True}


@router.post("/nisr/imports", status_code=201)
async def import_nisr_release(
    request: Request,
    file: UploadFile = File(...),
    source_release: str = Form(..., min_length=3, max_length=120),
    season: str = Form(..., min_length=8, max_length=32),
    admin: dict = Depends(require_role("admin")),
):
    """Validate and stage one normalized NISR district/crop/season CSV."""
    season = " ".join(season.strip().split())
    if not _SEASON_PATTERN.fullmatch(season):
        raise HTTPException(status_code=422, detail="Season must look like '2026 Season A'.")
    source_release = source_release.strip()
    if not source_release:
        raise HTTPException(status_code=422, detail="Enter the NISR release title or reference.")
    filename = Path(file.filename or "nisr-release.csv").name[:180]
    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=415, detail="Upload a CSV file.")
    maximum = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    raw = await file.read(maximum + 1)
    if len(raw) > maximum:
        raise HTTPException(status_code=413, detail=f"CSV exceeds the {settings.MAX_UPLOAD_SIZE_MB} MB upload limit.")
    if not raw:
        raise HTTPException(status_code=422, detail="The uploaded CSV is empty.")

    try:
        text = raw.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text, newline=""))
        if not reader.fieldnames:
            raise ValueError("CSV header row is missing.")
        columns = {str(name).strip().lower(): name for name in reader.fieldnames if name}
        required = {"district", "crop", "season", "yield_kg_ha"}
        missing = required - set(columns)
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}.")
        district_lookup = {row["district"].casefold(): row["district"] for row in RWANDA_DISTRICTS}
        normalized = []
        seen = set()
        errors = []

        def number(row, column, line, required_value=False, positive=False):
            original = columns.get(column)
            value = (row.get(original) or "").strip() if original else ""
            if not value:
                if required_value:
                    raise ValueError(f"row {line}: {column} is required")
                return None
            try:
                result = float(value.replace(",", ""))
            except ValueError:
                raise ValueError(f"row {line}: {column} must be numeric") from None
            if not math.isfinite(result) or (result <= 0 if positive else result < 0):
                condition = "greater than zero" if positive else "zero or greater"
                raise ValueError(f"row {line}: {column} must be {condition}")
            return result

        for line, row in enumerate(reader, start=2):
            if not any(str(value or "").strip() for value in row.values()):
                continue
            try:
                district_raw = (row.get(columns["district"]) or "").strip()
                district = district_lookup.get(district_raw.casefold())
                if not district:
                    raise ValueError(f"row {line}: unknown Rwanda district '{district_raw}'")
                crop = (row.get(columns["crop"]) or "").strip()
                if not crop or len(crop) > 120:
                    raise ValueError(f"row {line}: crop is required and must be at most 120 characters")
                row_season = " ".join((row.get(columns["season"]) or "").split())
                if row_season.casefold() != season.casefold():
                    raise ValueError(f"row {line}: season must match the uploaded release season '{season}'")
                key = (district.casefold(), crop.casefold(), season.casefold())
                if key in seen:
                    raise ValueError(f"row {line}: duplicate district/crop/season record")
                seen.add(key)
                normalized.append({
                    "district": district,
                    "crop": crop,
                    "season": season,
                    "yield_kg_ha": number(row, "yield_kg_ha", line, required_value=True, positive=True),
                    "production_mt": number(row, "production_mt", line),
                    "cultivated_area_ha": number(row, "cultivated_area_ha", line, positive=True),
                })
            except ValueError as exc:
                errors.append(str(exc))
                if len(errors) >= 10:
                    break
        if errors:
            suffix = " More row errors omitted." if len(errors) >= 10 else ""
            raise ValueError("; ".join(errors) + suffix)
        if not normalized:
            raise ValueError("CSV contains no data rows.")
        if len(normalized) > 20000:
            raise ValueError("A release may contain at most 20,000 records.")
    except (UnicodeDecodeError, csv.Error, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    digest = hashlib.sha256(raw).hexdigest()
    try:
        duplicate = crud.find_nisr_import_by_hash(digest)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="NISR import tables are unavailable. Apply migration 0007_nisr_imports.sql, then retry.",
        ) from exc
    if duplicate and duplicate.get("status") != "failed":
        raise HTTPException(status_code=409, detail="This exact file is already staged or active.")
    if duplicate:
        import_id = str(duplicate["id"])
        crud.delete_nisr_yield_records(import_id)
        import_record = crud.finish_nisr_import(
            import_id, "staging", source_filename=filename,
            source_release=source_release, season=season,
            row_count=len(normalized), imported_by=str(admin.get("role") or "admin"),
            error_detail=None, activated_at=None,
        )
        if not import_record:
            raise HTTPException(status_code=503, detail="The previous failed import could not be reopened.")
    else:
        import_record = crud.create_nisr_import({
            "source_filename": filename,
            "source_release": source_release,
            "season": season,
            "sha256": digest,
            "status": "staging",
            "row_count": len(normalized),
            "imported_by": str(admin.get("role") or "admin"),
        })
    import_id = str(import_record["id"])
    try:
        crud.insert_nisr_yield_records([{"import_id": import_id, **row} for row in normalized])
        activated = crud.finish_nisr_import(
            import_id, "active", activated_at=datetime.now(timezone.utc).isoformat()
        )
        if not activated:
            raise RuntimeError("Import activation did not return a database record")
    except Exception as exc:
        logger.exception("NISR dataset import failed for %s", import_id)
        try:
            crud.delete_nisr_yield_records(import_id)
            crud.finish_nisr_import(import_id, "failed", error_detail="Dataset rows could not be fully committed.")
        except Exception:
            logger.exception("Could not clean up failed NISR import %s", import_id)
        raise HTTPException(status_code=500, detail="The release could not be committed; no partial dataset was activated.") from exc

    audit_admin_action("import_nisr_release", "nisr_imports", {
        "import_id": import_id, "season": season, "row_count": len(normalized), "sha256": digest,
    }, request=request)
    from app.ml.predict import invalidate_yield_evidence_cache
    invalidate_yield_evidence_cache()
    return {
        "id": import_id, "status": "active", "source_filename": filename,
        "source_release": source_release.strip(), "season": season,
        "rows_imported": len(normalized), "sha256": digest,
    }


@router.get("/nisr/imports")
def get_nisr_imports(_: dict = Depends(require_role("admin"))):
    try:
        return crud.list_nisr_imports()
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="NISR import tables are unavailable. Apply migration 0007_nisr_imports.sql.",
        ) from exc
