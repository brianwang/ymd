from datetime import datetime
from pydantic import BaseModel


class EventRegistrationCreate(BaseModel):
    name: str
    phone: str
    remark: str | None = None


class EventRegistrationOut(BaseModel):
    id: int
    event_id: int
    user_id: int
    name: str
    phone: str
    remark: str | None = None
    status: str
    created_at: datetime
    canceled_at: datetime | None = None

    class Config:
        from_attributes = True


class AdminEventRegistrationOut(EventRegistrationOut):
    pass

