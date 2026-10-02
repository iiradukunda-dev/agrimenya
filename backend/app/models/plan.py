from pydantic import BaseModel
from typing import Optional, Any
from uuid import UUID


class RoadmapStep(BaseModel):
    step_number: int
    title: str
    description: str
    timeframe: Optional[str] = None


class ResourceEstimate(BaseModel):
    seeds_kg: Optional[float] = None
    fertilizer_kg: Optional[float] = None
    irrigation_liters: Optional[float] = None
    estimated_cost_rwf: Optional[float] = None


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
