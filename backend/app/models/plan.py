from pydantic import BaseModel, Field
from typing import Optional, Any, Literal
from datetime import date
from uuid import UUID


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
