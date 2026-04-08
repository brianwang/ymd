from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import User as UserSchema, UserUpdate
from app.api.deps import get_current_active_user
import base64
from io import BytesIO
import qrcode

router = APIRouter()

@router.get("/me", response_model=UserSchema)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.put("/me", response_model=UserSchema)
async def update_user_me(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if user_in.nickname is not None:
        current_user.nickname = user_in.nickname
    if user_in.avatar_url is not None:
        current_user.avatar_url = user_in.avatar_url
    
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user

@router.get("/invite/qrcode")
async def invite_qrcode(current_user: User = Depends(get_current_active_user)):
    payload = f"ymd://invite?inviter_id={current_user.id}"
    img = qrcode.make(payload)
    buf = BytesIO()
    img.save(buf, format="PNG")
    png_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return {"inviter_id": current_user.id, "png_base64": png_base64}
