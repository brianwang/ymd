from __future__ import annotations

from datetime import datetime
from enum import Enum
import re
from pydantic import BaseModel, Field, field_validator, model_validator


class InquiryStatus(str, Enum):
    new = "new"
    contacted = "contacted"
    closed = "closed"


PHONE_RE = re.compile(r"^[0-9+\-() ]{7,32}$")


class InquiryCreateIn(BaseModel):
    contact_name: str | None = Field(default=None, max_length=50)
    contact_phone: str = Field(min_length=7, max_length=32)
    message: str = Field(min_length=1, max_length=1000)

    @field_validator("contact_name")
    @classmethod
    def _strip_name(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None

    @field_validator("contact_phone")
    @classmethod
    def _validate_phone(cls, v: str) -> str:
        s = v.strip()
        if not PHONE_RE.match(s):
            raise ValueError("invalid contact_phone")
        return s

    @field_validator("message")
    @classmethod
    def _strip_message(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("message required")
        return s


class InquiryCreateOut(BaseModel):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class InquiryAdminOut(BaseModel):
    id: int
    space_id: int
    user_id: int | None = None
    contact_name: str | None = None
    contact_phone: str
    message: str
    status: InquiryStatus
    admin_note: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class InquiryAdminListOut(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[InquiryAdminOut]


class InquiryAdminPatch(BaseModel):
    status: InquiryStatus | None = None
    admin_note: str | None = Field(default=None, max_length=2000)

    @field_validator("admin_note")
    @classmethod
    def _strip_note(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None

    @model_validator(mode="after")
    def _at_least_one_field(self) -> InquiryAdminPatch:
        if self.status is None and self.admin_note is None:
            raise ValueError("no fields to update")
        return self
