from pydantic import BaseModel
from typing import Optional, Literal
from uuid import UUID

RiskLevel = Literal["Low", "Medium", "High"]


class AlignmentMetric(BaseModel):
    id: Optional[UUID] = None
    zone_id: UUID
    season: str
    irrigation_ha: float = 0
    terraces_ha: float = 0
    credit_insurance_score: Optional[float] = None
    nutrition_risk_level: Optional[RiskLevel] = None
    climate_risk_level: Optional[RiskLevel] = None
    female_managed_share: Optional[float] = None
    export_readiness_flag: bool = False
    estimated_jobs_supported: int = 0


class NationalDashboardSummary(BaseModel):
    total_zones: int
    avg_irrigation_ha: float
    avg_terraces_ha: float
    avg_credit_insurance_score: float
    zones_high_nutrition_risk: int
    zones_high_climate_risk: int
    zones_export_ready: int
    total_estimated_jobs: int
