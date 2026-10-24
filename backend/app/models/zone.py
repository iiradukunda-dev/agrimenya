from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID


class ZoneCreate(BaseModel):
    district: str
    sector: Optional[str] = None
    cell: Optional[str] = None
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    crop_type: Optional[str] = None
    season: Optional[str] = None


class Zone(ZoneCreate):
    id: UUID


class AgriMetricCreate(BaseModel):
    zone_id: UUID
    season: str
    crop: str = "All crops"
    yield_actual: Optional[float] = Field(default=None, ge=0, le=1000000)
    production_mt: Optional[float] = Field(default=None, ge=0, le=100000000)
    rainfall_mm: Optional[float] = Field(default=None, ge=0, le=1000)
    soil_type: Optional[str] = None
    area_cultivated: Optional[float] = Field(default=None, gt=0, le=100000)
    household_size: Optional[float] = Field(default=None, gt=0, le=10000)


class AgriMetric(AgriMetricCreate):
    id: UUID
