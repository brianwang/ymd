from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.points_ledger import PointsLedger
from app.schemas.points import SignInResponse, PointsLedgerItem, PointsTaskItem
from app.services.points import (
    award_points,
    sign_in_biz_key,
    first_post_biz_key,
)
from app.services.ops_config import get_reward_config

router = APIRouter()

@router.post("/sign-in", response_model=SignInResponse)
async def sign_in(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    today = date.today()
    biz_key = sign_in_biz_key(today)
    cfg = await get_reward_config(db)
    new_points = await award_points(
        db=db,
        user_id=current_user.id,
        event_type="sign_in",
        biz_key=biz_key,
        delta=cfg["sign_in_points"],
    )
    await db.commit()
    if new_points is None:
        res = await db.execute(select(User.points).where(User.id == current_user.id))
        points = res.scalar_one()
        return {"awarded": False, "delta": 0, "points": points}
    return {"awarded": True, "delta": cfg["sign_in_points"], "points": new_points}

@router.get("/ledger", response_model=list[PointsLedgerItem])
async def ledger(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    q = (
        select(PointsLedger)
        .where(PointsLedger.user_id == current_user.id)
        .order_by(PointsLedger.created_at.desc(), PointsLedger.id.desc())
        .limit(limit)
        .offset(offset)
    )
    res = await db.execute(q)
    return list(res.scalars().all())

@router.get("/tasks", response_model=list[PointsTaskItem])
async def tasks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    today = date.today()
    cfg = await get_reward_config(db)
    sign_key = sign_in_biz_key(today)
    first_post_key = first_post_biz_key(current_user.id)
    q = (
        select(PointsLedger.biz_key)
        .where(
            PointsLedger.user_id == current_user.id,
            PointsLedger.biz_key.in_([sign_key, first_post_key]),
        )
    )
    res = await db.execute(q)
    existing = set(res.scalars().all())
    return [
        {
            "key": "sign_in",
            "title": "每日签到",
            "awarded": sign_key in existing,
            "delta": cfg["sign_in_points"],
        },
        {
            "key": "first_post",
            "title": "发布首帖",
            "awarded": first_post_key in existing,
            "delta": cfg["first_post_points"],
        },
    ]

@router.post("/first-post", response_model=SignInResponse)
async def first_post(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    biz_key = first_post_biz_key(current_user.id)
    cfg = await get_reward_config(db)
    new_points = await award_points(
        db=db,
        user_id=current_user.id,
        event_type="first_post",
        biz_key=biz_key,
        delta=cfg["first_post_points"],
    )
    await db.commit()
    if new_points is None:
        res = await db.execute(select(User.points).where(User.id == current_user.id))
        points = res.scalar_one()
        return {"awarded": False, "delta": 0, "points": points}
    return {"awarded": True, "delta": cfg["first_post_points"], "points": new_points}
