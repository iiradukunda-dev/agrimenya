from pydantic import BaseModel
from typing import Optional, Literal
from uuid import UUID

Severity = Literal["Info", "Warning", "Critical"]


class AlertCreate(BaseModel):
    zone_id: UUID
    message: str
    severity: Severity = "Info"
    created_by: Optional[str] = None


class Alert(AlertCreate):
    id: UUID
