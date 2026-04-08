from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from pydantic import BaseModel
from app.services.points import (
    award_points,
    invite_bind_biz_key,
)
from app.services.ops_config import get_reward_config
from pydantic import EmailStr

router = APIRouter()

class WxLoginRequest(BaseModel):
    code: str
    inviter_id: int | None = None

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int

@router.post("/wx-login", response_model=TokenResponse)
async def wx_login(req: WxLoginRequest, db: AsyncSession = Depends(get_db)):
    mock_openid = f"mock_openid_{req.code}"

    async with db.begin():
        result = await db.execute(select(User).filter(User.open_id == mock_openid))
        user = result.scalars().first()

        if not user:
            inviter = None
            if req.inviter_id is not None:
                inviter_res = await db.execute(select(User).where(User.id == req.inviter_id))
                inviter = inviter_res.scalars().first()
                if not inviter:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid inviter_id")
            user = User(
                open_id=mock_openid,
                nickname=f"用户_{req.code[:4]}",
                inviter_id=inviter.id if inviter else None,
            )
            db.add(user)
            await db.flush()
            if inviter:
                cfg = await get_reward_config(db)
                biz_key = invite_bind_biz_key(user.id)
                await award_points(
                    db=db,
                    user_id=inviter.id,
                    event_type="invite_reward_inviter",
                    biz_key=biz_key,
                    delta=cfg["inviter_reward_points"],
                )
                await award_points(
                    db=db,
                    user_id=user.id,
                    event_type="invite_reward_invitee",
                    biz_key=biz_key,
                    delta=cfg["invitee_reward_points"],
                )
    await db.refresh(user)

    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "user_id": user.id}

@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    email = req.email.strip().lower()
    async with db.begin():
        res = await db.execute(select(User.id).where(User.email == email))
        if res.first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        user = User(
            email=email,
            hashed_password=get_password_hash(req.password),
            nickname=email.split("@", 1)[0],
        )
        db.add(user)
        await db.flush()
    await db.refresh(user)
    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "user_id": user.id}

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    email = req.email.strip().lower()
    res = await db.execute(select(User).where(User.email == email))
    user = res.scalars().first()
    if not user or not user.hashed_password or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "user_id": user.id}
