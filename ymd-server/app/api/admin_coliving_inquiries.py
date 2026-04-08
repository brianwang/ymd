from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_superuser
from app.core.database import get_db
from app.models.inquiry import Inquiry
from app.models.user import User
from app.schemas.inquiry import InquiryAdminListOut, InquiryAdminOut, InquiryAdminPatch


router = APIRouter()


@router.get("/coliving/inquiries", response_model=InquiryAdminListOut)
async def list_inquiries(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status_filter: str | None = Query(None, alias="status"),
    keyword: str | None = Query(None),
    start_at: datetime | None = Query(None),
    end_at: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser),
):
    conditions = []
    if status_filter:
        conditions.append(Inquiry.status == status_filter.strip())
    if start_at:
        conditions.append(Inquiry.created_at >= start_at)
    if end_at:
        conditions.append(Inquiry.created_at <= end_at)
    if keyword:
        kw = keyword.strip()
        like = f"%{kw}%"
        ors = [
            Inquiry.contact_phone.ilike(like),
            Inquiry.contact_name.ilike(like),
            Inquiry.message.ilike(like),
            Inquiry.admin_note.ilike(like),
        ]
        if kw.isdigit():
            n = int(kw)
            if 0 <= n <= 2147483647:
                ors.append(Inquiry.id == n)
                ors.append(Inquiry.space_id == n)
        conditions.append(or_(*ors))

    where_clause = and_(*conditions) if conditions else None
    count_stmt = select(func.count(Inquiry.id))
    if where_clause is not None:
        count_stmt = count_stmt.where(where_clause)
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = select(Inquiry)
    if where_clause is not None:
        stmt = stmt.where(where_clause)
    stmt = stmt.order_by(Inquiry.created_at.desc(), Inquiry.id.desc()).limit(limit).offset(offset)
    res = await db.execute(stmt)
    items = list(res.scalars().all())
    return InquiryAdminListOut(
        total=total,
        limit=limit,
        offset=offset,
        items=[InquiryAdminOut.model_validate(x) for x in items],
    )


@router.patch("/coliving/inquiries/{inquiry_id}", response_model=InquiryAdminOut)
async def patch_inquiry(
    inquiry_id: int,
    body: InquiryAdminPatch,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser),
):
    values: dict = {"updated_at": func.now()}
    if body.status is not None:
        values["status"] = body.status.value
    if body.admin_note is not None:
        values["admin_note"] = body.admin_note
    stmt = update(Inquiry).where(Inquiry.id == inquiry_id).values(**values).returning(Inquiry)
    row = (await db.execute(stmt)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    await db.commit()
    return row[0]
