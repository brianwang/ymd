from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, delete, update, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.api.deps import get_current_active_user, get_current_user_optional
from app.core.database import get_db
from app.models.user import User
from app.models.post import Post
from app.models.comment import Comment
from app.models.post_like import PostLike
from app.models.post_favorite import PostFavorite
from app.schemas.post import PostCreate, PostOut, PostLikeToggleOut, PostFavoriteToggleOut, PostShareOut, MediaItem
from app.schemas.user import UserPublic
from app.schemas.comment import CommentCreate, CommentOut
from datetime import date
from app.services.post_tags import (
    TagRules,
    extract_hashtags_from_content,
    merge_explicit_and_parsed_tags,
    validate_tags,
)
from app.services.points import (
    award_points,
    can_award_daily,
    post_reward_biz_key,
    comment_reward_biz_key,
)
from app.services.ops_config import get_reward_config

router = APIRouter()

def _normalize_post_media(*, media: list | None, image_urls: list[str] | None) -> tuple[list[MediaItem], list[str]]:
    """
    兼容策略：
    - 优先使用 media（新字段）
    - 若 media 为空，则由 image_urls 生成 media(image)
    - 返回 (media_json, image_urls) 两者保持一致（image_urls 从 media 的 image 类型派生）
    """
    media_items: list[MediaItem] = []
    for item in (media or []):
        # DB/请求可能是 dict；统一解析为 MediaItem
        media_items.append(MediaItem.model_validate(item))

    if not media_items and image_urls:
        media_items = [MediaItem(type="image", url=u) for u in (image_urls or [])]
    normalized_image_urls = [m.url for m in media_items if m.type == "image"]
    # 对于极端兼容：media 没图但 image_urls 有图时，保留旧字段
    if not normalized_image_urls and image_urls:
        normalized_image_urls = list(image_urls)
    return (media_items, normalized_image_urls)

def _to_post_out(*, post: Post, author: UserPublic, liked_by_me: bool, favorited_by_me: bool) -> PostOut:
    media_items, image_urls = _normalize_post_media(media=getattr(post, "media", None), image_urls=getattr(post, "image_urls", None))
    return PostOut.model_validate(post).model_copy(
        update={
            "liked_by_me": liked_by_me,
            "favorited_by_me": favorited_by_me,
            "author": author,
            "media": media_items,
            "image_urls": image_urls,
            # 兜底：DB content 允许空字符串；若未来改为 nullable，此处也确保返回 string
            "content": (getattr(post, "content", "") or ""),
        }
    )

@router.get("/posts", response_model=List[PostOut])
async def list_posts(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: int | None = Query(None, ge=1),
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    conditions = [Post.deleted_at.is_(None)]
    if user_id is not None:
        conditions.append(Post.user_id == user_id)

    if current_user is None:
        stmt = (
            select(Post, User)
            .join(User, User.id == Post.user_id)
            .where(and_(*conditions))
            .order_by(Post.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(stmt)
        rows = result.all()
        items: List[PostOut] = []
        for post, author in rows:
            items.append(_to_post_out(post=post, author=UserPublic.model_validate(author), liked_by_me=False, favorited_by_me=False))
        return items

    stmt = (
        select(Post, User, PostLike.id, PostFavorite.id)
        .join(User, User.id == Post.user_id)
        .outerjoin(PostLike, and_(PostLike.post_id == Post.id, PostLike.user_id == current_user.id))
        .outerjoin(PostFavorite, and_(PostFavorite.post_id == Post.id, PostFavorite.user_id == current_user.id))
        .where(and_(*conditions))
        .order_by(Post.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    rows = result.all()
    items: List[PostOut] = []
    for post, author, like_id, fav_id in rows:
        items.append(_to_post_out(post=post, author=UserPublic.model_validate(author), liked_by_me=like_id is not None, favorited_by_me=fav_id is not None))
    return items

@router.post("/posts", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_in: PostCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    cfg = await get_reward_config(db)

    content = (post_in.content or "").strip()
    media_items, image_urls = _normalize_post_media(media=post_in.media, image_urls=post_in.image_urls)

    # tags：显式 + 正文解析 #标签 -> 合并去重归一化，并做数量/长度/字符校验
    parsed = extract_hashtags_from_content(content)
    merged = merge_explicit_and_parsed_tags(explicit=post_in.tags, parsed=parsed)
    try:
        tags = validate_tags(merged, rules=TagRules())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    location = post_in.location.model_dump() if post_in.location is not None else None

    post = Post(
        user_id=current_user.id,
        content=content,
        image_urls=image_urls,
        media=[m.model_dump() for m in media_items],
        location=location,
        tags=tags,
    )
    db.add(post)
    await db.flush()
    prefix = f"post_reward:{today.isoformat()}:"
    if await can_award_daily(
        db=db,
        user_id=current_user.id,
        event_type="post_reward",
        biz_key_prefix=prefix,
        limit=cfg["daily_post_reward_limit"],
    ):
        await award_points(
            db=db,
            user_id=current_user.id,
            event_type="post_reward",
            biz_key=post_reward_biz_key(today=today, post_id=post.id),
            delta=cfg["post_reward_points"],
        )
    await db.commit()
    await db.refresh(post)
    return _to_post_out(post=post, author=UserPublic.model_validate(current_user), liked_by_me=False, favorited_by_me=False)

@router.get("/posts/{post_id}", response_model=PostOut)
async def get_post(
    post_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    base_conditions = and_(Post.id == post_id, Post.deleted_at.is_(None))
    if current_user is None:
        stmt = select(Post, User).join(User, User.id == Post.user_id).where(base_conditions)
        result = await db.execute(stmt)
        row = result.first()
        if not row:
            raise HTTPException(status_code=404, detail="Post not found")
        post, author = row
        return _to_post_out(post=post, author=UserPublic.model_validate(author), liked_by_me=False, favorited_by_me=False)

    stmt = (
        select(Post, User, PostLike.id, PostFavorite.id)
        .join(User, User.id == Post.user_id)
        .outerjoin(PostLike, and_(PostLike.post_id == Post.id, PostLike.user_id == current_user.id))
        .outerjoin(PostFavorite, and_(PostFavorite.post_id == Post.id, PostFavorite.user_id == current_user.id))
        .where(base_conditions)
    )
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Post not found")
    post, author, like_id, fav_id = row
    return _to_post_out(post=post, author=UserPublic.model_validate(author), liked_by_me=like_id is not None, favorited_by_me=fav_id is not None)


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Post).where(and_(Post.id == post_id, Post.deleted_at.is_(None)))
    result = await db.execute(stmt)
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges")
    await db.execute(
        update(Post)
        .where(Post.id == post_id)
        .values(deleted_at=func.now())
        .returning(Post.id)
    )
    await db.commit()
    return


@router.post("/posts/{post_id}/like", response_model=PostLikeToggleOut)
async def like_post(
    post_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    exists_stmt = select(Post.id).where(and_(Post.id == post_id, Post.deleted_at.is_(None)))
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

    res = await db.execute(select(Post.like_count, Post.comment_count).where(Post.id == post_id))
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Post not found")
    like_count, comment_count = row
    return {"liked": True, "like_count": like_count, "comment_count": comment_count}


@router.delete("/posts/{post_id}/like", response_model=PostLikeToggleOut)
async def unlike_post(
    post_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    exists_stmt = select(Post.id).where(and_(Post.id == post_id, Post.deleted_at.is_(None)))
    exists_res = await db.execute(exists_stmt)
    if not exists_res.first():
        raise HTTPException(status_code=404, detail="Post not found")

    del_stmt = delete(PostLike).where(and_(PostLike.user_id == current_user.id, PostLike.post_id == post_id))
    del_res = await db.execute(del_stmt)
    if getattr(del_res, "rowcount", 0):
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

    res = await db.execute(select(Post.like_count, Post.comment_count).where(Post.id == post_id))
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Post not found")
    like_count, comment_count = row
    return {"liked": False, "like_count": like_count, "comment_count": comment_count}

@router.post("/posts/{post_id}/like/toggle", response_model=PostLikeToggleOut)
async def toggle_like(
    post_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
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
            .where(and_(Post.id == post_id, Post.deleted_at.is_(None)))
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

    del_stmt = delete(PostLike).where(and_(PostLike.user_id == current_user.id, PostLike.post_id == post_id))
    await db.execute(del_stmt)
    upd = (
        update(Post)
        .where(and_(Post.id == post_id, Post.deleted_at.is_(None)))
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
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    exists_stmt = select(Post.id).where(and_(Post.id == post_id, Post.deleted_at.is_(None)))
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
    cfg = await get_reward_config(db)
    exists_stmt = select(Post.id).where(and_(Post.id == post_id, Post.deleted_at.is_(None)))
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
        limit=cfg["daily_comment_reward_limit"],
    ):
        await award_points(
            db=db,
            user_id=current_user.id,
            event_type="comment_reward",
            biz_key=comment_reward_biz_key(today=today, comment_id=comment.id),
            delta=cfg["comment_reward_points"],
        )
    await db.commit()
    await db.refresh(comment)
    return comment

@router.post("/posts/{post_id}/favorite/toggle", response_model=PostFavoriteToggleOut)
async def toggle_favorite(
    post_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    insert_stmt = (
        pg_insert(PostFavorite)
        .values(user_id=current_user.id, post_id=post_id)
        .on_conflict_do_nothing(index_elements=["user_id", "post_id"])
        .returning(PostFavorite.id)
    )
    inserted = await db.execute(insert_stmt)
    inserted_id = inserted.scalar_one_or_none()
    if inserted_id is not None:
        upd = (
            update(Post)
            .where(and_(Post.id == post_id, Post.deleted_at.is_(None)))
            .values(favorite_count=Post.favorite_count + 1)
            .returning(Post.favorite_count)
        )
        res = await db.execute(upd)
        row = res.first()
        if not row:
            raise HTTPException(status_code=404, detail="Post not found")
        favorite_count = row[0]
        await db.commit()
        return {"favorited": True, "favorite_count": favorite_count}

    del_stmt = delete(PostFavorite).where(and_(PostFavorite.user_id == current_user.id, PostFavorite.post_id == post_id))
    await db.execute(del_stmt)
    upd = (
        update(Post)
        .where(and_(Post.id == post_id, Post.deleted_at.is_(None)))
        .values(favorite_count=func.greatest(Post.favorite_count - 1, 0))
        .returning(Post.favorite_count)
    )
    res = await db.execute(upd)
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Post not found")
    favorite_count = row[0]
    await db.commit()
    return {"favorited": False, "favorite_count": favorite_count}

@router.post("/posts/{post_id}/share", response_model=PostShareOut)
async def share_post(
    post_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    upd = (
        update(Post)
        .where(and_(Post.id == post_id, Post.deleted_at.is_(None)))
        .values(share_count=Post.share_count + 1)
        .returning(Post.share_count)
    )
    res = await db.execute(upd)
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Post not found")
    share_count = row[0]
    await db.commit()
    return {"share_count": share_count}
