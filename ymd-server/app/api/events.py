from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import and_, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import get_current_active_user, get_current_user_optional
from app.core.database import get_db
from app.models.event import Event
from app.models.event_registration import EventRegistration
from app.models.user import User
from app.schemas.event import EventListItem, EventOut
from app.schemas.event_registration import EventRegistrationCreate


router = APIRouter()


class EventDetailOut(EventOut):
    my_registration_status: str = "none"


class RegisterResult(BaseModel):
    registration_id: int
    status: str
    registered_count: int
    capacity: int | None = None


class CancelResult(BaseModel):
    status: str
    registered_count: int
    capacity: int | None = None


class MyRegistrationItem(BaseModel):
    registration_id: int
    status: str
    created_at: datetime
    canceled_at: datetime | None = None
    event: EventListItem


async def _cancel_registration(event_id: int, current_user: User, db: AsyncSession) -> CancelResult:
    now = datetime.now(timezone.utc)
    event_res = await db.execute(select(Event).where(Event.id == event_id).with_for_update())
    event = event_res.scalars().first()
    if not event or not event.is_published:
        raise HTTPException(status_code=404, detail="Event not found")

    reg_res = await db.execute(
        select(EventRegistration).where(
            and_(EventRegistration.event_id == event_id, EventRegistration.user_id == current_user.id)
        )
    )
    existing = reg_res.scalars().first()
    if not existing or existing.status != "registered":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not registered")

    await db.execute(
        update(EventRegistration)
        .where(EventRegistration.id == existing.id)
        .values(status="canceled", canceled_at=now)
    )

    upd = (
        update(Event)
        .where(Event.id == event_id)
        .values(registered_count=func.greatest(Event.registered_count - 1, 0))
        .returning(Event.registered_count, Event.capacity)
    )
    row = (await db.execute(upd)).first()
    new_count = int(row[0]) if row else event.registered_count

    await db.commit()
    return CancelResult(status="canceled", registered_count=new_count, capacity=event.capacity)


@router.get("/events", response_model=list[EventListItem])
async def list_events(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    category: str | None = Query(None),
    city: str | None = Query(None),
    start_from: datetime | None = Query(None),
    start_to: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Event).where(Event.is_published.is_(True))
    if category:
        stmt = stmt.where(Event.category == category)
    if city:
        stmt = stmt.where(Event.city == city)
    if start_from:
        stmt = stmt.where(Event.start_at >= start_from)
    if start_to:
        stmt = stmt.where(Event.start_at <= start_to)
    stmt = stmt.order_by(Event.start_at.asc(), Event.id.asc()).limit(limit).offset(offset)
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.get("/events/{event_id}", response_model=EventDetailOut)
async def get_event(
    event_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Event).where(and_(Event.id == event_id, Event.is_published.is_(True))))
    event = res.scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    my_status = "none"
    if current_user is not None:
        r = await db.execute(
            select(EventRegistration.status).where(
                and_(EventRegistration.event_id == event_id, EventRegistration.user_id == current_user.id)
            )
        )
        s = r.scalar_one_or_none()
        if s:
            my_status = s

    return EventDetailOut.model_validate(event).model_copy(update={"my_registration_status": my_status})


@router.post("/events/{event_id}/registrations", response_model=RegisterResult)
async def register_event(
    event_id: int,
    body: EventRegistrationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    name = body.name.strip()
    phone = body.phone.strip()
    remark = body.remark.strip() if body.remark else None
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name required")
    if not phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone required")

    event_res = await db.execute(select(Event).where(Event.id == event_id).with_for_update())
    event = event_res.scalars().first()
    if not event or not event.is_published:
        raise HTTPException(status_code=404, detail="Event not found")
    deadline = event.signup_deadline_at
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    if now > deadline:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Registration closed")

    reg_res = await db.execute(
        select(EventRegistration).where(
            and_(EventRegistration.event_id == event_id, EventRegistration.user_id == current_user.id)
        )
    )
    existing = reg_res.scalars().first()
    if existing and existing.status == "registered":
        await db.execute(
            update(EventRegistration)
            .where(EventRegistration.id == existing.id)
            .values(name=name, phone=phone, remark=remark)
        )
        return RegisterResult(
            registration_id=existing.id,
            status="registered",
            registered_count=event.registered_count,
            capacity=event.capacity,
        )

    if event.capacity is not None and event.registered_count >= event.capacity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Event full")

    if event.capacity is not None:
        upd = (
            update(Event)
            .where(and_(Event.id == event_id, Event.registered_count < Event.capacity))
            .values(registered_count=Event.registered_count + 1)
            .returning(Event.registered_count, Event.capacity)
        )
        row = (await db.execute(upd)).first()
        if not row:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Event full")
        new_count = int(row[0])
    else:
        upd = (
            update(Event)
            .where(Event.id == event_id)
            .values(registered_count=Event.registered_count + 1)
            .returning(Event.registered_count)
        )
        new_count = int((await db.execute(upd)).scalar_one())

    if existing:
        upd_reg = (
            update(EventRegistration)
            .where(EventRegistration.id == existing.id)
            .values(
                name=name,
                phone=phone,
                remark=remark,
                status="registered",
                canceled_at=None,
            )
            .returning(EventRegistration.id)
        )
        registration_id = int((await db.execute(upd_reg)).scalar_one())
    else:
        reg = EventRegistration(
            event_id=event_id,
            user_id=current_user.id,
            name=name,
            phone=phone,
            remark=remark,
            status="registered",
        )
        db.add(reg)
        await db.flush()
        registration_id = int(reg.id)

    await db.commit()

    return RegisterResult(
        registration_id=registration_id,
        status="registered",
        registered_count=new_count,
        capacity=event.capacity,
    )


@router.post("/events/{event_id}/registrations/cancel", response_model=CancelResult)
async def cancel_registration(
    event_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await _cancel_registration(event_id=event_id, current_user=current_user, db=db)


@router.delete("/events/{event_id}/registrations/me", response_model=CancelResult)
async def cancel_registration_me(
    event_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await _cancel_registration(event_id=event_id, current_user=current_user, db=db)


@router.get("/events/registrations/me", response_model=list[MyRegistrationItem])
async def my_registrations(
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
    items: list[MyRegistrationItem] = []
    for reg, event in rows:
        items.append(
            MyRegistrationItem(
                registration_id=reg.id,
                status=reg.status,
                created_at=reg.created_at,
                canceled_at=reg.canceled_at,
                event=EventListItem.model_validate(event),
            )
        )
    return items
