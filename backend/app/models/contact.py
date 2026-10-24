from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


ContactRole = Literal["planner", "extension_officer", "cooperative_leader", "farmer", "other"]


class ContactCreate(BaseModel):
    display_name: str | None = Field(default=None, max_length=120)
    role: ContactRole | None = None
    phone: str | None = Field(default=None, max_length=40)
    bsuid: str | None = Field(default=None, min_length=1, max_length=255)
    language: Literal["en", "rw"] = "en"
    zone_id: UUID | None = None
    crops: list[str] = Field(default_factory=list, max_length=30)


class ContactOut(BaseModel):
    id: UUID
    display_name: str | None = None
    role: ContactRole | None = None
    phone_masked: str | None = None
    language: Literal["en", "rw"] = "en"
    zone_id: UUID | None = None
    crops: list[str] = Field(default_factory=list)
    whatsapp_opt_in: bool = False
    opt_in_at: str | None = None
    opt_in_source: str | None = None
    opt_in_text_version: str | None = None
    opt_out_at: str | None = None
    last_inbound_at: str | None = None
    deleted_at: str | None = None


class OptInRequest(BaseModel):
    source: str = Field(..., min_length=1, max_length=80)
    text_version: str = Field(..., min_length=1, max_length=80)


class SubscriptionIn(BaseModel):
    zone_id: UUID | None = None
    crop: str | None = Field(default=None, max_length=80)
    min_severity: Literal["info", "warning", "critical"] = "warning"


class SubscriptionOut(SubscriptionIn):
    id: UUID
    contact_id: UUID
