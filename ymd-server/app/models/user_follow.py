from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.sql import func

from app.models.base import Base


class UserFollow(Base):
    __tablename__ = "user_follows"

    id = Column(Integer, primary_key=True)
    follower_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    following_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("follower_user_id", "following_user_id", name="uq_user_follows_pair"),
        Index("ix_user_follows_follower_created_at", "follower_user_id", "created_at"),
        Index("ix_user_follows_following_created_at", "following_user_id", "created_at"),
    )

