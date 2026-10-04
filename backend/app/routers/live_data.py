from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.field_report_service import list_field_reports, submit_field_report
from app.services.live_data_service import build_live_context
from app.services.weather_service import fetch_weather

router = APIRouter(prefix="/live", tags=["Live Data"])


class FieldReportRequest(BaseModel):
    zone_id: str
    district: str = Field(..., min_length=1, max_length=100)
    crop: str = Field(..., min_length=1, max_length=50)
    rainfall_mm: float | None = None
    soil_moisture_pct: float | None = None
    symptoms: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=1000)


class LiveContextRequest(BaseModel):
    zone_id: str | None = None
    district: str | None = None
    crop: str | None = None
    rainfall_mm: float | None = None
    notes: str | None = Field(default=None, max_length=1000)


@router.get("/weather/{district}")
def get_weather(district: str):
    return fetch_weather(district=district)


@router.post("/field-report")
def create_field_report(request: FieldReportRequest):
    return submit_field_report(
        zone_id=request.zone_id,
        district=request.district,
        crop=request.crop,
        rainfall_mm=request.rainfall_mm,
        soil_moisture_pct=request.soil_moisture_pct,
        symptoms=request.symptoms,
        notes=request.notes,
    )


@router.get("/field-reports/{zone_id}")
def get_field_reports(zone_id: str):
    return list_field_reports(zone_id=zone_id, limit=20)


@router.post("/context")
def live_context(request: LiveContextRequest):
    if not request.district and not request.zone_id:
        raise HTTPException(status_code=400, detail="Provide either district or zone_id.")
    return build_live_context(
        zone_id=request.zone_id,
        district=request.district,
        crop=request.crop,
        rainfall_mm=request.rainfall_mm,
        notes=request.notes,
    )
