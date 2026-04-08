from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Index
from sqlalchemy.sql import func
from app.models.base import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False, index=True)
    category = Column(String, nullable=False, index=True)
    city = Column(String, nullable=False, index=True)
    address = Column(String, nullable=True)
    cover_url = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    start_at = Column(DateTime(timezone=True), nullable=False, index=True)
    end_at = Column(DateTime(timezone=True), nullable=True)
    signup_deadline_at = Column(DateTime(timezone=True), nullable=False, index=True)
    capacity = Column(Integer, nullable=True)
    registered_count = Column(Integer, nullable=False, server_default="0")
    is_published = Column(Boolean, nullable=False, server_default="false", index=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("ix_events_published_start_at", "is_published", "start_at"),
    )

