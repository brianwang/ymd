from datetime import date
from sqlalchemy import update, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from app.models.user import User
from app.models.points_ledger import PointsLedger
from app.core.config import settings

SIGN_IN_POINTS = settings.SIGN_IN_POINTS
INVITER_REWARD_POINTS = settings.INVITER_REWARD_POINTS
INVITEE_REWARD_POINTS = settings.INVITEE_REWARD_POINTS
FIRST_POST_POINTS = settings.FIRST_POST_POINTS
POST_REWARD_POINTS = settings.POST_REWARD_POINTS
COMMENT_REWARD_POINTS = settings.COMMENT_REWARD_POINTS
DAILY_POST_REWARD_LIMIT = settings.DAILY_POST_REWARD_LIMIT
DAILY_COMMENT_REWARD_LIMIT = settings.DAILY_COMMENT_REWARD_LIMIT

async def award_points(
    db: AsyncSession,
    user_id: int,
    event_type: str,
    biz_key: str,
    delta: int,
) -> int | None:
    stmt = (
        insert(PointsLedger)
        .values(user_id=user_id, event_type=event_type, biz_key=biz_key, delta=delta)
        .on_conflict_do_nothing(constraint="uq_points_ledger_user_biz_key")
        .returning(PointsLedger.id)
    )
    res = await db.execute(stmt)
    inserted = res.scalar_one_or_none()
    if inserted is None:
        return None
    upd = (
        update(User)
        .where(User.id == user_id)
        .values(points=User.points + delta)
        .returning(User.points)
    )
    res2 = await db.execute(upd)
    return res2.scalar_one()

def sign_in_biz_key(today: date) -> str:
    return f"sign_in:{today.isoformat()}"

def invite_bind_biz_key(invitee_user_id: int) -> str:
    return f"invite_bind:{invitee_user_id}"

def first_post_biz_key(user_id: int) -> str:
    return f"first_post:{user_id}"

def post_reward_biz_key(today: date, post_id: int) -> str:
    return f"post_reward:{today.isoformat()}:{post_id}"

def comment_reward_biz_key(today: date, comment_id: int) -> str:
    return f"comment_reward:{today.isoformat()}:{comment_id}"

async def can_award_daily(
    db: AsyncSession,
    user_id: int,
    event_type: str,
    biz_key_prefix: str,
    limit: int,
) -> bool:
    stmt = (
        select(func.count())
        .select_from(PointsLedger)
        .where(
            PointsLedger.user_id == user_id,
            PointsLedger.event_type == event_type,
            PointsLedger.biz_key.like(f"{biz_key_prefix}%"),
        )
    )
    res = await db.execute(stmt)
    return int(res.scalar_one() or 0) < limit
