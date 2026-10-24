from pydantic import BaseModel, Field
from typing import Optional, Literal
from uuid import UUID

Severity = Literal["Info", "Warning", "Critical"]


class AlertCreate(BaseModel):
    zone_id: UUID
    message: str = Field(..., min_length=1, max_length=2000)
    severity: Severity = "Info"
    crop: str | None = Field(default=None, max_length=80)
    action: str | None = Field(default=None, max_length=500)
    created_by: Optional[str] = Field(default=None, max_length=120)


class Alert(AlertCreate):
    id: UUID
