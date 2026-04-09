from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel, field_validator

from app.utils.geo import validate_lat_lng


class PreferredLocation(BaseModel):
    lat: float
    lng: float
    display_name: Optional[str] = None
    city: Optional[str] = None
    source: Optional[Literal["manual", "device"]] = None
    updated_at: Optional[datetime] = None


class UserPreferredLocationUpdate(BaseModel):
    lat: float
    lng: float
    display_name: str
    city: Optional[str] = None
    source: Literal["manual", "device"] = "manual"

    @field_validator("display_name")
    @classmethod
    def _display_name_non_empty(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("display_name required")
        if len(v) > 100:
            raise ValueError("display_name too long")
        return v

    @field_validator("lat")
    @classmethod
    def _lat_range(cls, v: float) -> float:
        validate_lat_lng(lat=v, lng=0.0)
        return v

    @field_validator("lng")
    @classmethod
    def _lng_range(cls, v: float) -> float:
        validate_lat_lng(lat=0.0, lng=v)
        return v

class UserBase(BaseModel):
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

class UserCreate(UserBase):
    open_id: Optional[str] = None
    union_id: Optional[str] = None

class UserUpdate(UserBase):
    pass

class UserInDBBase(UserBase):
    id: int
    open_id: Optional[str] = None
    is_active: bool
    points: int
    inviter_id: Optional[int] = None
    phone: Optional[str] = None
    preferred_location: Optional[PreferredLocation] = None

    class Config:
        from_attributes = True

class User(UserInDBBase):
    pass


class UserPublic(BaseModel):
    id: int
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


class UserProfileOut(UserPublic):
    viewer_is_following: bool = False


class FollowStateOut(BaseModel):
    target_user_id: int
    viewer_is_following: bool
