from datetime import datetime
from pydantic import BaseModel

class SignInResponse(BaseModel):
    awarded: bool
    delta: int
    points: int

class PointsLedgerItem(BaseModel):
    id: int
    event_type: str
    biz_key: str
    delta: int
    created_at: datetime

    class Config:
        from_attributes = True

class PointsTaskItem(BaseModel):
    key: str
    title: str
    awarded: bool
    delta: int
