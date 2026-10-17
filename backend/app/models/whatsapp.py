from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class AlertApprovalOut(BaseModel):
    id: UUID
    status: Literal["approved"]
    approved_by: str
    approved_at: datetime


class DispatchSummary(BaseModel):
    queued: int = 0
    sent: int = 0
    failed: int = 0
    skipped_no_consent: int = 0
    skipped_no_template: int = 0
    skipped_daily_cap: int = 0
    by_error_code: dict[str, int] = Field(default_factory=dict)


class DeliveryCounts(BaseModel):
    queued: int = 0
    sent: int = 0
    delivered: int = 0
    read: int = 0
    failed: int = 0


class AlertDeliveryOut(BaseModel):
    alert_id: UUID
    counts: DeliveryCounts


class WhatsAppHealth(BaseModel):
    mode: Literal["mock", "live"]
    approved_templates: int
    last_webhook_received_at: datetime | None
    failed_messages_24h: int


class WhatsAppStats(BaseModel):
    days: int
    by_status: dict[str, int]
    by_kind: dict[str, int]
    top_error_codes: dict[str, int]


class WhatsAppTemplateOut(BaseModel):
    name: str
    language: str
    category: str
    status: str
    body_preview: str | None
    param_count: int


class TemplatePreviewRequest(BaseModel):
    params: list[str] = Field(..., min_length=1, max_length=10)


class TemplatePreviewOut(BaseModel):
    name: str
    language: str
    body_preview: str
