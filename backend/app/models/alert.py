from typing import Literal
from uuid import UUID

from pydantic import BaseModel

Severity = Literal["Info", "Warning", "Critical"]


class AlertCreate(BaseModel):
    zone_id: UUID
    message: str
    severity: Severity = "Info"
    created_by: str | None = None


class Alert(AlertCreate):
    id: UUID
