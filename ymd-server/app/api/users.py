from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.event import Event
from app.models.event_registration import EventRegistration
from app.models.user import User
from app.models.user_follow import UserFollow
from app.schemas.event import EventListItem
from app.schemas.user import (
    User as UserSchema,
    UserUpdate,
    UserProfileOut,
    UserPublic,
    FollowStateOut,
    PreferredLocation,
    UserPreferredLocationUpdate,
)
from app.api.deps import get_current_active_user, get_current_user_optional
import base64
from io import BytesIO
import qrcode
from pydantic import BaseModel, EmailStr
from app.core.security import get_password_hash

router = APIRouter()

class BindEmailRequest(BaseModel):
    email: EmailStr
    password: str

@router.get("/me", response_model=UserSchema)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.get("/me/location", response_model=PreferredLocation | None, response_model_exclude_none=True)
async def get_my_preferred_location(current_user: User = Depends(get_current_active_user)):
    return current_user.preferred_location


@router.put("/me/location", response_model=PreferredLocation, response_model_exclude_none=True)
async def put_my_preferred_location(
    body: UserPreferredLocationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    # Persist to dedicated columns for proximity queries/auditing
    current_user.preferred_location_lat = body.lat
    current_user.preferred_location_lng = body.lng
    current_user.preferred_location_display_name = body.display_name
    current_user.preferred_location_city = body.city
    current_user.preferred_location_source = body.source
    current_user.preferred_location_updated_at = datetime.now(timezone.utc)

    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    # property guaranteed not None after update
    return current_user.preferred_location

@router.put("/me", response_model=UserSchema)
async def update_user_me(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if user_in.nickname is not None:
        nickname = user_in.nickname.strip()
        if not nickname or len(nickname) < 2 or len(nickname) > 20:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid nickname")
        current_user.nickname = nickname
    if user_in.avatar_url is not None:
        current_user.avatar_url = user_in.avatar_url
    if user_in.phone is not None:
        phone = user_in.phone.strip()
        if phone == "":
            current_user.phone = None
        else:
            if not phone.isdigit() or len(phone) != 11:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid phone")
            current_user.phone = phone
    
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user

@router.post("/bind-email", response_model=UserSchema)
async def bind_email(
    req: BindEmailRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    email = req.email.strip().lower()
    if current_user.email and current_user.email != email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already bound")
    res = await db.execute(select(User.id).where(User.email == email, User.id != current_user.id))
    if res.first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")
    current_user.email = email
    current_user.hashed_password = get_password_hash(req.password)
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


class MyEventRegistrationItem(BaseModel):
    registration_id: int
    status: str
    created_at: datetime
    canceled_at: datetime | None = None
    event: EventListItem


@router.get("/me/event-registrations", response_model=list[MyEventRegistrationItem])
async def my_event_registrations(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    include_canceled: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(EventRegistration, Event)
        .join(Event, Event.id == EventRegistration.event_id)
        .where(EventRegistration.user_id == current_user.id)
        .where(Event.is_published.is_(True))
        .order_by(EventRegistration.created_at.desc(), EventRegistration.id.desc())
        .limit(limit)
        .offset(offset)
    )
    if not include_canceled:
        stmt = stmt.where(EventRegistration.status == "registered")
    res = await db.execute(stmt)
    rows = res.all()
    items: list[MyEventRegistrationItem] = []
    for reg, event in rows:
        items.append(
            MyEventRegistrationItem(
                registration_id=reg.id,
                status=reg.status,
                created_at=reg.created_at,
                canceled_at=reg.canceled_at,
                event=EventListItem.model_validate(event),
            )
        )
    return items


@router.get("/{user_id}", response_model=UserProfileOut)
async def read_user_profile(
    user_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    viewer_is_following = False
    if current_user and current_user.id != user_id:
        res = await db.execute(
            select(UserFollow.id).where(
                and_(
                    UserFollow.follower_user_id == current_user.id,
                    UserFollow.following_user_id == user_id,
                )
            )
        )
        viewer_is_following = res.first() is not None

    base = UserPublic.model_validate(user)
    return UserProfileOut(**base.model_dump(), viewer_is_following=viewer_is_following)


@router.post("/{target_user_id}/follow", response_model=FollowStateOut)
async def follow_user(
    target_user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if target_user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot follow yourself")

    res = await db.execute(select(User.id).where(User.id == target_user_id))
    if not res.first():
        raise HTTPException(status_code=404, detail="User not found")

    stmt = (
        pg_insert(UserFollow)
        .values(follower_user_id=current_user.id, following_user_id=target_user_id)
        .on_conflict_do_nothing(index_elements=["follower_user_id", "following_user_id"])
    )
    await db.execute(stmt)
    await db.commit()
    return {"target_user_id": target_user_id, "viewer_is_following": True}


@router.delete("/{target_user_id}/follow", response_model=FollowStateOut)
async def unfollow_user(
    target_user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if target_user_id == current_user.id:
        return {"target_user_id": target_user_id, "viewer_is_following": False}

    await db.execute(
        delete(UserFollow).where(
            and_(
                UserFollow.follower_user_id == current_user.id,
                UserFollow.following_user_id == target_user_id,
            )
        )
    )
    await db.commit()
    return {"target_user_id": target_user_id, "viewer_is_following": False}
