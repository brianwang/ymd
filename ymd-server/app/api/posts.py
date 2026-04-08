from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, delete, update, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.user import User
from app.models.post import Post
from app.models.comment import Comment
from app.models.post_like import PostLike
from app.schemas.post import PostCreate, PostOut, PostLikeToggleOut
from app.schemas.comment import CommentCreate, CommentOut
from datetime import date
from app.services.points import (
    POST_REWARD_POINTS,
    COMMENT_REWARD_POINTS,
    DAILY_POST_REWARD_LIMIT,
    DAILY_COMMENT_REWARD_LIMIT,
    award_points,
    can_award_daily,
    post_reward_biz_key,
    comment_reward_biz_key,
)

router = APIRouter()

@router.get("/posts", response_model=List[PostOut])
async def list_posts(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Post, PostLike.id)
        .outerjoin(PostLike, and_(PostLike.post_id == Post.id, PostLike.user_id == current_user.id))
        .order_by(Post.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    rows = result.all()
    items: List[PostOut] = []
    for post, like_id in rows:
        items.append(PostOut.model_validate(post).model_copy(update={"liked_by_me": like_id is not None}))
    return items

@router.post("/posts", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_in: PostCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    post = Post(
        user_id=current_user.id,
        content=post_in.content,
        image_urls=post_in.image_urls,
    )
    db.add(post)
    await db.flush()
    prefix = f"post_reward:{today.isoformat()}:"
    if await can_award_daily(
        db=db,
        user_id=current_user.id,
        event_type="post_reward",
        biz_key_prefix=prefix,
        limit=DAILY_POST_REWARD_LIMIT,
    ):
        await award_points(
            db=db,
            user_id=current_user.id,
            event_type="post_reward",
            biz_key=post_reward_biz_key(today=today, post_id=post.id),
            delta=POST_REWARD_POINTS,
        )
    await db.commit()
    await db.refresh(post)
    return PostOut.model_validate(post).model_copy(update={"liked_by_me": False})

@router.get("/posts/{post_id}", response_model=PostOut)
async def get_post(
    post_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Post, PostLike.id)
        .outerjoin(PostLike, and_(PostLike.post_id == Post.id, PostLike.user_id == current_user.id))
        .where(Post.id == post_id)
    )
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Post not found")
    post, like_id = row
    return PostOut.model_validate(post).model_copy(update={"liked_by_me": like_id is not None})

@router.post("/posts/{post_id}/like", response_model=PostLikeToggleOut)
async def toggle_like(
    post_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    exists_stmt = select(Post.id).where(Post.id == post_id)
    exists_res = await db.execute(exists_stmt)
    if not exists_res.first():
        raise HTTPException(status_code=404, detail="Post not found")

    insert_stmt = (
        pg_insert(PostLike)
        .values(user_id=current_user.id, post_id=post_id)
        .on_conflict_do_nothing(index_elements=["user_id", "post_id"])
        .returning(PostLike.id)
    )
    inserted = await db.execute(insert_stmt)
    inserted_id = inserted.scalar_one_or_none()

    if inserted_id is not None:
        upd = (
            update(Post)
            .where(Post.id == post_id)
            .values(like_count=Post.like_count + 1)
            .returning(Post.like_count, Post.comment_count)
        )
        res = await db.execute(upd)
        row = res.first()
        if not row:
            raise HTTPException(status_code=404, detail="Post not found")
        like_count, comment_count = row
        await db.commit()
        return {"liked": True, "like_count": like_count, "comment_count": comment_count}

    del_stmt = delete(PostLike).where(
        and_(PostLike.user_id == current_user.id, PostLike.post_id == post_id)
    )
    await db.execute(del_stmt)
    upd = (
        update(Post)
        .where(Post.id == post_id)
        .values(like_count=func.greatest(Post.like_count - 1, 0))
        .returning(Post.like_count, Post.comment_count)
    )
    res = await db.execute(upd)
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Post not found")
    like_count, comment_count = row
    await db.commit()
    return {"liked": False, "like_count": like_count, "comment_count": comment_count}

@router.get("/posts/{post_id}/comments", response_model=List[CommentOut])
async def list_comments(
    post_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    exists_stmt = select(Post.id).where(Post.id == post_id)
    exists_res = await db.execute(exists_stmt)
    if not exists_res.first():
        raise HTTPException(status_code=404, detail="Post not found")
    stmt = (
        select(Comment)
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at.asc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/posts/{post_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
async def create_comment(
    post_id: int,
    comment_in: CommentCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    exists_stmt = select(Post.id).where(Post.id == post_id)
    exists_res = await db.execute(exists_stmt)
    if not exists_res.first():
        raise HTTPException(status_code=404, detail="Post not found")

    comment = Comment(
        post_id=post_id,
        user_id=current_user.id,
        content=comment_in.content,
    )
    db.add(comment)
    await db.flush()
    upd = (
        update(Post)
        .where(Post.id == post_id)
        .values(comment_count=Post.comment_count + 1)
        .returning(Post.id)
    )
    await db.execute(upd)
    prefix = f"comment_reward:{today.isoformat()}:"
    if await can_award_daily(
        db=db,
        user_id=current_user.id,
        event_type="comment_reward",
        biz_key_prefix=prefix,
        limit=DAILY_COMMENT_REWARD_LIMIT,
    ):
        await award_points(
            db=db,
            user_id=current_user.id,
            event_type="comment_reward",
            biz_key=comment_reward_biz_key(today=today, comment_id=comment.id),
            delta=COMMENT_REWARD_POINTS,
        )
    await db.commit()
    await db.refresh(comment)
    return comment
