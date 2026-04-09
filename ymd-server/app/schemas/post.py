from typing import List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, model_validator

from app.schemas.user import UserPublic

class MediaItem(BaseModel):
    type: Literal["image", "video", "audio"]
    url: str

class PostCreate(BaseModel):
    # 兼容期：允许纯媒体帖，因此 content 可为空/缺省；最终落库会用空字符串代替 None
    content: Optional[str] = None
    # 兼容旧字段：继续支持 image_urls 的入参
    image_urls: List[str] = []
    # 新字段：统一媒体表达
    media: List[MediaItem] = []

    @model_validator(mode="after")
    def validate_content_or_media(self):
        content_ok = bool((self.content or "").strip())
        media_ok = bool(self.media) or bool(self.image_urls)
        if not content_ok and not media_ok:
            raise ValueError("发帖失败：文字或至少一个媒体(media/image_urls)必填")
        return self

class PostBase(BaseModel):
    id: int
    user_id: int
    content: str
    image_urls: List[str]
    media: List[MediaItem] = []
    like_count: int
    comment_count: int
    favorite_count: int
    share_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PostOut(PostBase):
    liked_by_me: bool = False
    favorited_by_me: bool = False
    author: Optional[UserPublic] = None

class PostLikeToggleOut(BaseModel):
    liked: bool
    like_count: int
    comment_count: int

class PostFavoriteToggleOut(BaseModel):
    favorited: bool
    favorite_count: int

class PostShareOut(BaseModel):
    share_count: int
