from datetime import datetime
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import delete, select, update, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_active_superuser
from app.core.database import get_db
from app.models.user import User
from app.models.post import Post
from app.models.comment import Comment
from app.models.post_like import PostLike
from app.models.points_ledger import PointsLedger
from app.schemas.points import PointsLedgerItem
from app.services.points import award_points
from app.services.ops_config import get_reward_config, upsert_reward_config

router = APIRouter()

class AdminUserOut(BaseModel):
    id: int
    email: str | None = None
    open_id: str | None = None
    nickname: str | None = None
    is_active: bool
    is_superuser: bool
    points: int

    class Config:
        from_attributes = True

class AdminPostOut(BaseModel):
    id: int
    user_id: int
    content: str
    like_count: int
    comment_count: int

    class Config:
        from_attributes = True

class AdminCommentOut(BaseModel):
    id: int
    post_id: int
    user_id: int
    content: str

    class Config:
        from_attributes = True

class SetActiveRequest(BaseModel):
    is_active: bool

class SetSuperuserRequest(BaseModel):
    is_superuser: bool

class AdjustPointsRequest(BaseModel):
    delta: int

class RewardConfigPatch(BaseModel):
    sign_in_points: int | None = None
    inviter_reward_points: int | None = None
    invitee_reward_points: int | None = None
    first_post_points: int | None = None
    post_reward_points: int | None = None
    comment_reward_points: int | None = None
    daily_post_reward_limit: int | None = None
    daily_comment_reward_limit: int | None = None

@router.get("/users", response_model=list[AdminUserOut])
async def list_users(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    q: str | None = Query(None),
    is_active: bool | None = Query(None),
    is_superuser: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser),
):
    stmt = select(User)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                User.email.ilike(like),
                User.open_id.ilike(like),
                User.nickname.ilike(like),
            )
        )
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    if is_superuser is not None:
        stmt = stmt.where(User.is_superuser == is_superuser)
    stmt = stmt.order_by(User.id.desc()).limit(limit).offset(offset)
    res = await db.execute(stmt)
    return list(res.scalars().all())

@router.patch("/users/{user_id}/active", response_model=AdminUserOut)
async def set_user_active(
    user_id: int,
    body: SetActiveRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser),
):
    stmt = (
        update(User)
        .where(User.id == user_id)
        .values(is_active=body.is_active)
        .returning(User)
    )
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    await db.commit()
    return row[0]

@router.patch("/users/{user_id}/superuser", response_model=AdminUserOut)
async def set_user_superuser(
    user_id: int,
    body: SetSuperuserRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser),
):
    stmt = (
        update(User)
        .where(User.id == user_id)
        .values(is_superuser=body.is_superuser)
        .returning(User)
    )
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    await db.commit()
    return row[0]

@router.post("/users/{user_id}/points-adjust")
async def adjust_points(
    user_id: int,
    body: AdjustPointsRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser),
):
    exists = await db.execute(select(User.id).where(User.id == user_id))
    if not exists.first():
        raise HTTPException(status_code=404, detail="User not found")
    biz_key = f"admin_adjust:{admin.id}:{uuid4().hex}"
    new_points = await award_points(
        db=db,
        user_id=user_id,
        event_type="admin_adjust",
        biz_key=biz_key,
        delta=body.delta,
    )
    await db.commit()
    if new_points is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Points adjustment failed")
    return {"user_id": user_id, "delta": body.delta, "points": new_points}

@router.get("/users/{user_id}/ledger", response_model=list[PointsLedgerItem])
async def user_ledger(
    user_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    event_type: str | None = Query(None),
    start_at: datetime | None = Query(None),
    end_at: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser),
):
    exists = await db.execute(select(User.id).where(User.id == user_id))
    if not exists.first():
        raise HTTPException(status_code=404, detail="User not found")

    stmt = select(PointsLedger).where(PointsLedger.user_id == user_id)
    if event_type:
        stmt = stmt.where(PointsLedger.event_type == event_type)
    if start_at:
        stmt = stmt.where(PointsLedger.created_at >= start_at)
    if end_at:
        stmt = stmt.where(PointsLedger.created_at <= end_at)

    stmt = (
        stmt.order_by(PointsLedger.created_at.desc(), PointsLedger.id.desc())
        .limit(limit)
        .offset(offset)
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())

@router.get("/posts", response_model=list[AdminPostOut])
async def list_posts(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    q: str | None = Query(None),
    user_id: int | None = Query(None, ge=1),
    start_at: datetime | None = Query(None),
    end_at: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser),
):
    stmt = select(Post)
    if q:
        stmt = stmt.where(Post.content.ilike(f"%{q.strip()}%"))
    if user_id is not None:
        stmt = stmt.where(Post.user_id == user_id)
    if start_at:
        stmt = stmt.where(Post.created_at >= start_at)
    if end_at:
        stmt = stmt.where(Post.created_at <= end_at)
    stmt = stmt.order_by(Post.created_at.desc(), Post.id.desc()).limit(limit).offset(offset)
    res = await db.execute(stmt)
    return list(res.scalars().all())

@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser),
):
    exists = await db.execute(select(Post.id).where(Post.id == post_id))
    if not exists.first():
        raise HTTPException(status_code=404, detail="Post not found")
    await db.execute(delete(Comment).where(Comment.post_id == post_id))
    await db.execute(delete(PostLike).where(PostLike.post_id == post_id))
    await db.execute(delete(Post).where(Post.id == post_id))
    await db.commit()
    return {"deleted": True, "post_id": post_id}

@router.get("/comments", response_model=list[AdminCommentOut])
async def list_comments(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    q: str | None = Query(None),
    user_id: int | None = Query(None, ge=1),
    post_id: int | None = Query(None, ge=1),
    start_at: datetime | None = Query(None),
    end_at: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser),
):
    stmt = select(Comment)
    if q:
        stmt = stmt.where(Comment.content.ilike(f"%{q.strip()}%"))
    if user_id is not None:
        stmt = stmt.where(Comment.user_id == user_id)
    if post_id is not None:
        stmt = stmt.where(Comment.post_id == post_id)
    if start_at:
        stmt = stmt.where(Comment.created_at >= start_at)
    if end_at:
        stmt = stmt.where(Comment.created_at <= end_at)
    stmt = stmt.order_by(Comment.created_at.desc(), Comment.id.desc()).limit(limit).offset(offset)
    res = await db.execute(stmt)
    return list(res.scalars().all())

@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser),
):
    res = await db.execute(select(Comment.post_id).where(Comment.id == comment_id))
    post_id = res.scalar_one_or_none()
    if post_id is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    await db.execute(delete(Comment).where(Comment.id == comment_id))
    await db.execute(
        update(Post)
        .where(Post.id == post_id)
        .values(comment_count=func.greatest(Post.comment_count - 1, 0))
    )
    await db.commit()
    return {"deleted": True, "comment_id": comment_id}

@router.get("/reward-config")
async def get_reward_cfg(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser),
):
    return await get_reward_config(db)

@router.put("/reward-config")
async def put_reward_cfg(
    patch: RewardConfigPatch,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser),
):
    saved = await upsert_reward_config(db, patch.model_dump())
    await db.commit()
    return saved
