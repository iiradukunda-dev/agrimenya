from uuid import UUID

from pydantic import BaseModel


class ZoneCreate(BaseModel):
    district: str
    sector: str | None = None
    cell: str | None = None
    latitude: float
    longitude: float
    crop_type: str | None = None
    season: str | None = None


class Zone(ZoneCreate):
    id: UUID


class AgriMetricCreate(BaseModel):
    zone_id: UUID
    season: str
    crop: str = "All crops"
    yield_actual: float | None = None
    production_mt: float | None = None
    rainfall_mm: float | None = None
    soil_type: str | None = None
    area_cultivated: float | None = None
    household_size: float | None = None


class AgriMetric(AgriMetricCreate):
    id: UUID
