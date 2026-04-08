from datetime import datetime
from pydantic import BaseModel


class EventListItem(BaseModel):
    id: int
    title: str
    category: str
    city: str
    cover_url: str | None = None
    start_at: datetime
    end_at: datetime | None = None
    signup_deadline_at: datetime
    capacity: int | None = None
    registered_count: int

    class Config:
        from_attributes = True


class EventOut(EventListItem):
    address: str | None = None
    summary: str | None = None
    content: str | None = None


class EventAdminUpsert(BaseModel):
    title: str
    category: str
    city: str
    address: str | None = None
    cover_url: str | None = None
    summary: str | None = None
    content: str | None = None
    start_at: datetime
    end_at: datetime | None = None
    signup_deadline_at: datetime
    capacity: int | None = None


class EventAdminOut(EventOut):
    is_published: bool
    published_at: datetime | None = None

