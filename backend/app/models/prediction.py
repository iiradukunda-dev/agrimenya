from typing import Literal
from uuid import UUID

from pydantic import BaseModel

PriorityLevel = Literal["Low", "Medium", "High"]


class PredictionRequest(BaseModel):
    zone_id: UUID
    season: str
    crop: str = "All crops"
    rainfall_mm: float | None = None
    area_cultivated: float | None = None
    soil_type: str | None = None
    household_size: float | None = None


class PredictionResult(BaseModel):
    zone_id: UUID
    season: str
    crop: str
    predicted_yield: float
    priority_level: PriorityLevel
    confidence: float
    model_version: str
    # analysis-only fields
    yield_per_ha: float | None = None
    benchmark_yield_per_ha: float | None = None
    yield_gap_kg_ha: float | None = None
    yield_index: float | None = None


class PredictionRecord(PredictionResult):
    id: UUID
