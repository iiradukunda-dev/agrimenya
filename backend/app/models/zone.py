from math import isfinite
from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel, Field, model_validator


class FieldBoundary(BaseModel):
    """A farmer-drawn GeoJSON polygon; this is not a cadastral boundary."""
    type: Literal["Polygon"]
    coordinates: list[list[tuple[float, float]]]

    @model_validator(mode="after")
    def validate_single_rwanda_ring(self):
        if len(self.coordinates) != 1:
            raise ValueError("A field outline must contain one closed outer ring")
        ring = self.coordinates[0]
        if len(ring) < 4 or ring[0] != ring[-1]:
            raise ValueError("A field outline must have at least three points and close back to its first point")
        if len(ring) > 501:
            raise ValueError("A field outline can contain at most 500 distinct points")
        for longitude, latitude in ring:
            if not isfinite(longitude) or not isfinite(latitude):
                raise ValueError("Field outline coordinates must be finite numbers")
            if not (28 <= longitude <= 32 and -5 <= latitude <= 1):
                raise ValueError("Field outline coordinates must be within Rwanda")
        return self


class ZoneCreate(BaseModel):
    district: str = Field(min_length=1, max_length=100)
    sector: Optional[str] = Field(default=None, max_length=100)
    cell: Optional[str] = Field(default=None, max_length=100)
    site_name: Optional[str] = Field(default=None, max_length=80)
    latitude: float = Field(ge=-5, le=1)
    longitude: float = Field(ge=28, le=32)
    field_boundary_geojson: Optional[FieldBoundary] = None
    crop_type: Optional[str] = Field(default=None, max_length=100)
    season: Optional[str] = Field(default=None, max_length=100)


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
