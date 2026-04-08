from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from app.models.base import Base

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_comments_post_created_at", "post_id", "created_at"),
        Index("ix_comments_user_created_at", "user_id", "created_at"),
    )
