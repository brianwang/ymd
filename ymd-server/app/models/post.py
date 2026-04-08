from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Index, JSON
from sqlalchemy.sql import func
from app.models.base import Base

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    image_urls = Column(JSON, nullable=False, server_default="[]")
    # Rich media attachments. Each item: {"type": "image"|"video"|"audio", "url": "..."}
    media = Column(JSON, nullable=False, server_default="[]")
    like_count = Column(Integer, nullable=False, server_default="0")
    comment_count = Column(Integer, nullable=False, server_default="0")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_posts_created_at", "created_at"),
        Index("ix_posts_user_created_at", "user_id", "created_at"),
    )
