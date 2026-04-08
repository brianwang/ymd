from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

class PostCreate(BaseModel):
    content: str
    image_urls: List[str] = []

class PostBase(BaseModel):
    id: int
    user_id: int
    content: str
    image_urls: List[str]
    like_count: int
    comment_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PostOut(PostBase):
    liked_by_me: bool = False

class PostLikeToggleOut(BaseModel):
    liked: bool
    like_count: int
    comment_count: int
