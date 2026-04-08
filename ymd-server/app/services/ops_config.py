from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models.ops_config import OpsConfig

REWARDS_KEY = "rewards"

def default_reward_config() -> dict:
    return {
        "sign_in_points": settings.SIGN_IN_POINTS,
        "inviter_reward_points": settings.INVITER_REWARD_POINTS,
        "invitee_reward_points": settings.INVITEE_REWARD_POINTS,
        "first_post_points": settings.FIRST_POST_POINTS,
        "post_reward_points": settings.POST_REWARD_POINTS,
        "comment_reward_points": settings.COMMENT_REWARD_POINTS,
        "daily_post_reward_limit": settings.DAILY_POST_REWARD_LIMIT,
        "daily_comment_reward_limit": settings.DAILY_COMMENT_REWARD_LIMIT,
    }

def _normalize_reward_value(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    try:
        return int(value)
    except Exception:
        return None

async def get_reward_config(db: AsyncSession) -> dict:
    res = await db.execute(select(OpsConfig.value).where(OpsConfig.key == REWARDS_KEY))
    raw = res.scalar_one_or_none()
    cfg = default_reward_config()
    if isinstance(raw, dict):
        for k in cfg.keys():
            if k in raw:
                v = _normalize_reward_value(raw.get(k))
                if v is not None:
                    cfg[k] = v
    return cfg

async def upsert_reward_config(db: AsyncSession, patch: dict) -> dict:
    current = await get_reward_config(db)
    merged = dict(current)
    for k, v in patch.items():
        nv = _normalize_reward_value(v)
        if nv is not None and k in merged:
            merged[k] = nv
    stmt = (
        insert(OpsConfig)
        .values(key=REWARDS_KEY, value=merged)
        .on_conflict_do_update(
            index_elements=["key"],
            set_={"value": merged, "updated_at": func.now()},
        )
        .returning(OpsConfig.value)
    )
    res = await db.execute(stmt)
    saved = res.scalar_one()
    return saved
