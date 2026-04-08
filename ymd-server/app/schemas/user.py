from typing import Optional
from pydantic import BaseModel

class UserBase(BaseModel):
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    email: Optional[str] = None

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
