from typing import Optional
from pydantic import BaseModel

class UserBase(BaseModel):
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None

class UserCreate(UserBase):
    open_id: str
    union_id: Optional[str] = None

class UserUpdate(UserBase):
    pass

class UserInDBBase(UserBase):
    id: int
    open_id: str
    is_active: bool
    points: int
    inviter_id: Optional[int] = None

    class Config:
        from_attributes = True

class User(UserInDBBase):
    pass
