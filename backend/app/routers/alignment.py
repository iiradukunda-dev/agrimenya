from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from uuid import UUID
from app.core.auth import require_user
from app.db import crud
from app.services.alignment_calculator import calculate_alignment_metrics
from app.ml.predict import get_yield_index

router = APIRouter(prefix="/alignment", tags=["National Alignment"])

FINANCE_EVIDENCE_KEYS = {
    "member_registration", "land_or_tenure_records", "production_history",
    "sales_records", "bank_or_sacco_statement", "loan_repayment_history",
    "group_savings_or_guarantee",
}
EXPORT_EVIDENCE_KEYS = {
    "cooperative_registration", "traceability_records", "quality_grading_records",
    "phytosanitary_documents", "buyer_contract_or_order", "certification_records",
}


class ReadinessChecklistUpdate(BaseModel):
    finance_evidence: dict[str, bool] | None = None
    export_evidence: dict[str, bool] | None = None


class WorkRecordCreate(BaseModel):
    season: str = Field(min_length=1, max_length=40)
    crop: str = Field(min_length=1, max_length=80)
    worker_days: float = Field(ge=0, le=1_000_000)
    notes: str = Field(default="", max_length=1000)


@router.post("/compute/{zone_id}")
def compute_alignment(zone_id: UUID, season: str, predicted_yield: float,
                       area_cultivated: float | None = None, rainfall_mm: float | None = None,
                       priority_level: str = "Medium", crop: str | None = None, district: str | None = None,
                       _: dict = Depends(require_user)):
    zone = crud.get_zone(zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    # obtain yield_index from predict module (district+crop) instead of
    # recomputing yield logic here.
    yield_index = None
    try:
        if crop and district:
            yield_index = get_yield_index(district, crop, season)
    except Exception:
        yield_index = None

    metrics = calculate_alignment_metrics(predicted_yield, area_cultivated, rainfall_mm, priority_level, yield_index)
    record = {"zone_id": zone_id, "season": season, **metrics}
    return crud.upsert_alignment_metric(record)


@router.get("/finance-readiness/{zone_id}")
def finance_readiness(zone_id: UUID, _: dict = Depends(require_user)):
    metric = crud.get_alignment_metric(zone_id)
    if not metric:
        raise HTTPException(status_code=404, detail="No alignment data for this zone yet")
    return {"zone_id": zone_id, "credit_insurance_score": None, "status": "unavailable",
            "note": "No validated credit-readiness method is configured."}


@router.get("/nutrition-risk/{zone_id}")
def nutrition_risk(zone_id: UUID, _: dict = Depends(require_user)):
    metric = crud.get_alignment_metric(zone_id)
    if not metric:
        raise HTTPException(status_code=404, detail="No alignment data for this zone yet")
    return {"zone_id": zone_id, "nutrition_risk_level": None, "status": "unavailable",
            "note": "District crop yield alone does not establish household nutrition risk."}


@router.get("/export-flags")
def export_flags(_: dict = Depends(require_user)):
    # Older stored flags came from an unvalidated threshold heuristic.
    return []


@router.get("/readiness/{zone_id}")
def get_readiness(zone_id: UUID, _: dict = Depends(require_user)):
    if not crud.get_zone(zone_id):
        raise HTTPException(status_code=404, detail="Zone not found")
    record = crud.get_zone_readiness(zone_id) or {}
    finance = record.get("finance_evidence") or {}
    export = record.get("export_evidence") or {}
    return {
        "zone_id": str(zone_id),
        "finance_evidence": finance,
        "export_evidence": export,
        "finance_checklist": _checklist_summary(finance, FINANCE_EVIDENCE_KEYS),
        "export_checklist": _checklist_summary(export, EXPORT_EVIDENCE_KEYS),
        "updated_at": record.get("updated_at"),
        "interpretation": "Checklist completion tracks evidence recorded here; it is not a credit score or export approval.",
    }


def _checklist_summary(values: dict, expected: set[str]) -> dict:
    completed = sum(values.get(key) is True for key in expected)
    return {"completed_items": completed, "total_items": len(expected),
            "completion_percent": round(completed * 100 / len(expected)) if expected else 0}


@router.put("/readiness/{zone_id}")
def update_readiness(zone_id: UUID, payload: ReadinessChecklistUpdate,
                     _: dict = Depends(require_user)):
    if not crud.get_zone(zone_id):
        raise HTTPException(status_code=404, detail="Zone not found")
    finance = payload.finance_evidence or {}
    export = payload.export_evidence or {}
    if set(finance) - FINANCE_EVIDENCE_KEYS or set(export) - EXPORT_EVIDENCE_KEYS:
        raise HTTPException(status_code=422, detail="Checklist contains unsupported evidence fields")
    existing = crud.get_zone_readiness(zone_id) or {}
    merged_finance = {**(existing.get("finance_evidence") or {}), **finance}
    merged_export = {**(existing.get("export_evidence") or {}), **export}
    crud.upsert_zone_readiness(zone_id, merged_finance, merged_export)
    return get_readiness(zone_id, {})


@router.get("/work-records/{zone_id}")
def get_work_records(zone_id: UUID, _: dict = Depends(require_user)):
    if not crud.get_zone(zone_id):
        raise HTTPException(status_code=404, detail="Zone not found")
    return crud.list_zone_work_records(zone_id)


@router.post("/work-records/{zone_id}")
def create_work_record(zone_id: UUID, payload: WorkRecordCreate,
                       _: dict = Depends(require_user)):
    if not crud.get_zone(zone_id):
        raise HTTPException(status_code=404, detail="Zone not found")
    record = crud.create_zone_work_record({"zone_id": str(zone_id), **payload.model_dump()})
    return {**record, "basis": "Observed worker-days entered by a user; this is not an estimate of jobs supported."}


@router.get("/dashboard")
def national_dashboard(_: dict = Depends(require_user)):
    metrics = crud.list_alignment_metrics()
    work_records = crud.list_zone_work_records()
    if not metrics:
        return {"total_zones": 0, "estimate_status": "unavailable_pending_validated_data_and_methods",
                "message": "Validated national alignment metrics are not configured.",
                "observed_worker_days": round(sum(float(row.get("worker_days") or 0) for row in work_records), 2),
                "work_record_count": len(work_records),
                "work_record_basis": "Observed person-days submitted by users; not estimated jobs supported."}

    total = len(metrics)

    return {
        "total_zones": total,
        "avg_irrigation_ha": None,
        "avg_terraces_ha": None,
        "avg_credit_insurance_score": None,
        "zones_high_nutrition_risk": None,
        "zones_high_climate_risk": None,
        "zones_export_ready": None,
        "total_estimated_jobs": None,
        "estimate_status": "unavailable_pending_validated_data_and_methods",
        "observed_worker_days": round(sum(float(row.get("worker_days") or 0) for row in work_records), 2),
        "work_record_count": len(work_records),
        "work_record_basis": "Observed person-days submitted by users; not estimated jobs supported.",
    }
