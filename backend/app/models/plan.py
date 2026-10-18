from pydantic import BaseModel, Field
from typing import Optional, Any
from uuid import UUID


class RoadmapStep(BaseModel):
    step_number: int
    title: str
    description: str
    timeframe: Optional[str] = None


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
    basis: Optional[str] = None


class PlanCreate(BaseModel):
    zone_id: UUID
    title: str
    roadmap: list[RoadmapStep]
    resources: ResourceEstimate
    created_by: Optional[str] = None


class Plan(BaseModel):
    id: UUID
    zone_id: UUID
    title: str
    roadmap_json: Any
    resources_json: Any
    created_by: Optional[str] = None
