from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.sql import func
from app.models.base import Base


class EventRegistration(Base):
    __tablename__ = "event_registrations"

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    remark = Column(Text, nullable=True)
    status = Column(String, nullable=False, server_default="registered", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    canceled_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("event_id", "user_id", name="uq_event_registrations_event_user"),
        Index("ix_event_registrations_event_status", "event_id", "status"),
        Index("ix_event_registrations_user_status", "user_id", "status"),
    )

