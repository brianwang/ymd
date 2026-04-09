from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_superuser
from app.core.database import get_db
from app.models.event import Event
from app.models.event_registration import EventRegistration
from app.models.user import User
from app.schemas.event import EventAdminOut, EventAdminUpsert
from app.schemas.event_registration import AdminEventRegistrationOut


router = APIRouter()


class PublishPatch(BaseModel):
    is_published: bool


@router.get("/events", response_model=list[EventAdminOut])
async def list_events(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    q: str | None = Query(None),
    is_published: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser),
):
    stmt = select(Event)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Event.title.ilike(like),
                Event.city.ilike(like),
                Event.category.ilike(like),
            )
        )
    if is_published is not None:
        stmt = stmt.where(Event.is_published == is_published)
    stmt = stmt.order_by(Event.start_at.desc(), Event.id.desc()).limit(limit).offset(offset)
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.post("/events", response_model=EventAdminOut, status_code=status.HTTP_201_CREATED)
async def create_event(
    body: EventAdminUpsert,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser),
):
    event = Event(
        title=body.title.strip(),
        category=body.category.strip(),
        city=body.city.strip(),
        address=body.address.strip() if body.address else None,
        lat=body.lat,
        lng=body.lng,
        cover_url=body.cover_url.strip() if body.cover_url else None,
        summary=body.summary,
        content=body.content,
        start_at=body.start_at,
        end_at=body.end_at,
        signup_deadline_at=body.signup_deadline_at,
        capacity=body.capacity,
        is_published=False,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


@router.put("/events/{event_id}", response_model=EventAdminOut)
async def update_event(
    event_id: int,
    body: EventAdminUpsert,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser),
):
    res = await db.execute(select(Event).where(Event.id == event_id))
    event = res.scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if body.capacity is not None and event.registered_count > body.capacity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Capacity less than registered_count")

    stmt = (
        update(Event)
        .where(Event.id == event_id)
        .values(
            title=body.title.strip(),
            category=body.category.strip(),
            city=body.city.strip(),
            address=body.address.strip() if body.address else None,
            lat=body.lat,
            lng=body.lng,
            cover_url=body.cover_url.strip() if body.cover_url else None,
            summary=body.summary,
            content=body.content,
            start_at=body.start_at,
            end_at=body.end_at,
            signup_deadline_at=body.signup_deadline_at,
            capacity=body.capacity,
        )
        .returning(Event)
    )
    row = (await db.execute(stmt)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Event not found")
    await db.commit()
    return row[0]


@router.patch("/events/{event_id}/publish", response_model=EventAdminOut)
async def publish_event(
    event_id: int,
    body: PublishPatch,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser),
):
    values = {"is_published": body.is_published}
    if body.is_published:
        values["published_at"] = datetime.utcnow()
    else:
        values["published_at"] = None
    stmt = update(Event).where(Event.id == event_id).values(**values).returning(Event)
    row = (await db.execute(stmt)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Event not found")
    await db.commit()
    return row[0]


@router.get("/events/{event_id}/registrations", response_model=list[AdminEventRegistrationOut])
async def list_registrations(
    event_id: int,
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser),
):
    exists = await db.execute(select(Event.id).where(Event.id == event_id))
    if not exists.first():
        raise HTTPException(status_code=404, detail="Event not found")

    stmt = select(EventRegistration).where(EventRegistration.event_id == event_id)
    if status_filter:
        stmt = stmt.where(EventRegistration.status == status_filter)
    stmt = (
        stmt.order_by(EventRegistration.created_at.desc(), EventRegistration.id.desc())
        .limit(limit)
        .offset(offset)
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())
