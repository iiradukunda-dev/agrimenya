from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any, Literal
from datetime import date
from math import isfinite
from uuid import UUID


class FertilizerResourceInput(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    rate_per_ha: float = Field(ge=0, allow_inf_nan=False)
    unit: Literal["kg", "litres", "tonnes"] = "kg"
    price_per_unit: Optional[float] = Field(default=None, ge=0, allow_inf_nan=False)

    @field_validator("name")
    @classmethod
    def strip_product_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Fertilizer product name cannot be blank")
        return value


class FertilizerResourceEstimate(FertilizerResourceInput):
    quantity: float = Field(ge=0, allow_inf_nan=False)
    estimated_cost_rwf: Optional[float] = Field(default=None, ge=0, allow_inf_nan=False)
    missing_price: bool = False


class ResourceEstimateRequest(BaseModel):
    area_cultivated: Optional[float] = Field(default=None, ge=0, allow_inf_nan=False)
    rainfall_mm: Optional[float] = Field(default=None, ge=0, allow_inf_nan=False)
    inputs: dict[str, float] = Field(default_factory=dict)
    fertilizer_items: list[FertilizerResourceInput] = Field(default_factory=list, max_length=8)
    area_source: Optional[str] = Field(default=None, max_length=40)
    rate_source: Optional[str] = Field(default=None, max_length=200)
    price_source: Optional[str] = Field(default=None, max_length=200)
    prices_checked_on: Optional[date] = None

    @field_validator("inputs")
    @classmethod
    def validate_resource_inputs(cls, values: dict[str, float]) -> dict[str, float]:
        from app.services.resource_estimator import RESOURCE_INPUT_KEYS

        unknown = set(values) - set(RESOURCE_INPUT_KEYS)
        if unknown:
            raise ValueError(f"Unknown resource inputs: {', '.join(sorted(unknown))}")
        if any(not isfinite(value) or value < 0 for value in values.values()):
            raise ValueError("Resource rates and prices must be finite and non-negative")
        return values


class RoadmapStep(BaseModel):
    step_number: int
    title: str
    description: str
    timeframe: Optional[str] = None
    owner: Optional[str] = Field(default=None, max_length=100)
    status: Literal["planned", "in_progress", "completed", "blocked"] = "planned"
    due_date: Optional[date] = None


class ResourceEstimate(BaseModel):
    area_ha: Optional[float] = None
    seeds_kg: Optional[float] = None
    fertilizer_kg: Optional[float] = None
    dap_kg: Optional[float] = None
    urea_kg: Optional[float] = None
    irrigation_liters: Optional[float] = None
    estimated_cost_rwf: Optional[float] = None
    status: Optional[str] = None
    user_inputs: dict[str, float] = Field(default_factory=dict)
    quantities: dict[str, float] = Field(default_factory=dict)
    costs_rwf: dict[str, float] = Field(default_factory=dict)
    fertilizer_items: list[FertilizerResourceEstimate] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)
    total_cost_scope: Optional[str] = None
    area_source: Optional[str] = None
    rate_source: Optional[str] = Field(default=None, max_length=200)
    price_source: Optional[str] = Field(default=None, max_length=200)
    prices_checked_on: Optional[str] = Field(default=None, max_length=10)
    basis: Optional[str] = None


class PlanCreate(BaseModel):
    zone_id: UUID
    title: str
    roadmap: list[RoadmapStep]
    resources: ResourceEstimate
    scenario: Literal["season_start", "priority_followup", "field_observation_followup", "cooperative_input_readiness", "custom"] = "custom"
    crop: Optional[str] = Field(default=None, max_length=50)
    season: Optional[str] = Field(default=None, max_length=80)
    decision_context: Optional[dict[str, Any]] = None
    created_by: Optional[str] = None


class Plan(BaseModel):
    id: UUID
    zone_id: UUID
    title: str
    roadmap_json: Any
    resources_json: Any
    created_by: Optional[str] = None
    scenario: Literal["season_start", "priority_followup", "field_observation_followup", "cooperative_input_readiness", "custom"] = "custom"
    crop: Optional[str] = None
    season: Optional[str] = None
