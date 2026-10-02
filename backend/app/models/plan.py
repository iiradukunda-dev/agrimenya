from typing import Any
from uuid import UUID

from pydantic import BaseModel


class RoadmapStep(BaseModel):
    step_number: int
    title: str
    description: str
    timeframe: str | None = None


class ResourceEstimate(BaseModel):
    seeds_kg: float | None = None
    fertilizer_kg: float | None = None
    irrigation_liters: float | None = None
    estimated_cost_rwf: float | None = None


class PlanCreate(BaseModel):
    zone_id: UUID
    title: str
    roadmap: list[RoadmapStep]
    resources: ResourceEstimate
    created_by: str | None = None


class Plan(BaseModel):
    id: UUID
    zone_id: UUID
    title: str
    roadmap_json: Any
    resources_json: Any
    created_by: str | None = None
