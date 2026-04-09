from typing import Any, List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field, model_validator

from app.schemas.user import UserPublic
from app.utils.geo import validate_lat_lng

class MediaItem(BaseModel):
    type: Literal["image", "video", "audio"]
    url: str


class PostLocation(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    address: Optional[str] = Field(default=None, max_length=200)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    raw: Optional[dict[str, Any]] = None

class PostCreate(BaseModel):
    content: Optional[str] = None
    image_urls: List[str] = []
    media: List[MediaItem] = []
    location: Optional[PostLocation] = None
    tags: List[str] = []
    lat: Optional[float] = None
    lng: Optional[float] = None
    city: Optional[str] = None

    @model_validator(mode="after")
    def validate_content_or_media(self):
        content_ok = bool((self.content or "").strip())
        media_ok = bool(self.media) or bool(self.image_urls)
        if not content_ok and not media_ok:
            raise ValueError("发帖失败：文字或至少一个媒体(media/image_urls)必填")
        return self

    @model_validator(mode="after")
    def validate_location_fields(self):
        if (self.lat is None) ^ (self.lng is None):
            raise ValueError("lat/lng 必须同时提供或同时为空")
        if self.lat is not None and self.lng is not None:
            validate_lat_lng(lat=self.lat, lng=self.lng)

        if self.location is not None and self.location.latitude is not None and self.location.longitude is not None:
            validate_lat_lng(lat=self.location.latitude, lng=self.location.longitude)
            if self.lat is None and self.lng is None:
                self.lat = self.location.latitude
                self.lng = self.location.longitude
            else:
                if abs(self.lat - self.location.latitude) > 1e-7 or abs(self.lng - self.location.longitude) > 1e-7:
                    raise ValueError("location.latitude/longitude 与 lat/lng 不一致")

        if self.city is not None:
            self.city = self.city.strip() or None
        return self

class PostBase(BaseModel):
    id: int
    user_id: int
    content: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    city: Optional[str] = None
    image_urls: List[str]
    media: List[MediaItem] = []
    location: Optional[PostLocation] = None
    tags: List[str] = []
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


class PostOutWithDistance(PostOut):
    distance_km: float

class PostLikeToggleOut(BaseModel):
    liked: bool
    like_count: int
    comment_count: int

class PostFavoriteToggleOut(BaseModel):
    favorited: bool
    favorite_count: int

class PostShareOut(BaseModel):
    share_count: int
