from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.sql import func
from app.models.base import Base

class PointsLedger(Base):
    __tablename__ = "points_ledger"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    biz_key = Column(String, nullable=False)
    delta = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "biz_key", name="uq_points_ledger_user_biz_key"),
        Index("ix_points_ledger_user_created_at", "user_id", "created_at"),
    )
