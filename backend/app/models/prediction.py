from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from uuid import UUID

PriorityLevel = Literal["Low", "Medium", "High", "Uncertain"]


class PredictionRequest(BaseModel):
    zone_id: UUID
    season: str = Field(min_length=2, max_length=40)
    crop: str = Field(default="All crops", min_length=1, max_length=80)
    crop_category: Optional[str] = Field(default=None, max_length=80)
    allow_category_proxy: bool = False
    rainfall_mm: Optional[float] = Field(default=None, ge=0, le=1000)
    area_cultivated: Optional[float] = Field(default=None, gt=0, le=100000)
    soil_type: Optional[str] = Field(default=None, max_length=100)
    household_size: Optional[float] = Field(default=None, gt=0, le=10000)

    @field_validator("season", "crop", "crop_category", "soil_type")
    @classmethod
    def normalize_text_inputs(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None


class PredictionResult(BaseModel):
    zone_id: UUID
    season: str
    crop: str
    predicted_yield: Optional[float] = None
    priority_level: Literal["Low", "Medium", "High", "Uncertain", "Unknown"]
    confidence: float
    confidence_basis: Optional[str] = None
    model_version: str
    model_trained_on: dict = Field(default_factory=lambda: {"data_hash": None, "date": None})
    basis: Literal["model", "baseline", "category_proxy"] = "baseline"
    yield_data_status: Literal["available", "no_data", "category_proxy"] = "available"
    district_observations: int = 0
    thin: bool = False
    warning: Optional[str] = None
    predicted_yield_low: Optional[float] = None
    predicted_yield_high: Optional[float] = None
    interval_level: Optional[float] = None
    explanation_factors: list[dict] = Field(default_factory=list)
    expected_yield_given_inputs_kg_ha: Optional[float] = None
    actual_yield_kg_ha: Optional[float] = None
    explanation_diagnosis: Optional[str] = None
    interpretation_note: Optional[str] = None
    priority_status: Optional[str] = None
    priority_reasons: list[str] = Field(default_factory=list)
    priority_components: dict = Field(default_factory=dict)
    priority_low_evidence: bool = False
    priority_fold_labels: list[str] = Field(default_factory=list)
    priority_changes_across_folds: int = 0
    # analysis-only fields
    yield_per_ha: Optional[float] = None
    benchmark_yield_per_ha: Optional[float] = None
    yield_gap_kg_ha: Optional[float] = None
    yield_index: Optional[float] = None


class PredictionRecord(PredictionResult):
    id: UUID
