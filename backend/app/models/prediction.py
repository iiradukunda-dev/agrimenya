from pydantic import BaseModel
from typing import Optional, Literal
from uuid import UUID

PriorityLevel = Literal["Low", "Medium", "High"]


class PredictionRequest(BaseModel):
    zone_id: UUID
    season: str
    crop: str = "All crops"
    rainfall_mm: Optional[float] = None
    area_cultivated: Optional[float] = None
    soil_type: Optional[str] = None
    household_size: Optional[float] = None


class PredictionResult(BaseModel):
    zone_id: UUID
    season: str
    crop: str
    predicted_yield: float
    priority_level: PriorityLevel
    confidence: float
    model_version: str


class PredictionRecord(PredictionResult):
    id: UUID
