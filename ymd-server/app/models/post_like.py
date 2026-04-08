from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.sql import func
from app.models.base import Base

class PostLike(Base):
    __tablename__ = "post_likes"

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "post_id", name="uq_post_likes_user_post"),
        Index("ix_post_likes_post_created_at", "post_id", "created_at"),
        Index("ix_post_likes_user_created_at", "user_id", "created_at"),
    )
