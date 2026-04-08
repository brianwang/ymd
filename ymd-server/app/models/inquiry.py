from sqlalchemy import Column, Integer, String, Text, DateTime, Index, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base


class Inquiry(Base):
    __tablename__ = "inquiries"

    id = Column(Integer, primary_key=True)
    space_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    contact_name = Column(String(50), nullable=True)
    contact_phone = Column(String(32), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, server_default="new", index=True)
    admin_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("ix_inquiries_space_created_at", "space_id", "created_at"),
        Index("ix_inquiries_status_created_at", "status", "created_at"),
    )
