from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID


class ZoneCreate(BaseModel):
    district: str
    sector: Optional[str] = None
    cell: Optional[str] = None
    latitude: float
    longitude: float
    crop_type: Optional[str] = None
    season: Optional[str] = None


class Zone(ZoneCreate):
    id: UUID


class AgriMetricCreate(BaseModel):
    zone_id: UUID
    season: str
    crop: str = "All crops"
    yield_actual: Optional[float] = None
    production_mt: Optional[float] = None
    rainfall_mm: Optional[float] = None
    soil_type: Optional[str] = None
    area_cultivated: Optional[float] = None
    household_size: Optional[float] = None


class AgriMetric(AgriMetricCreate):
    id: UUID
