from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_optional
from app.core.database import get_db
from app.models.inquiry import Inquiry
from app.models.user import User
from app.schemas.inquiry import InquiryCreateIn, InquiryCreateOut, InquiryStatus


router = APIRouter()


@router.post(
    "/coliving/spaces/{space_id}/inquiries",
    response_model=InquiryCreateOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_inquiry(
    space_id: int,
    body: InquiryCreateIn,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    inquiry = Inquiry(
        space_id=space_id,
        user_id=current_user.id if current_user else None,
        contact_name=body.contact_name,
        contact_phone=body.contact_phone,
        message=body.message,
        status=InquiryStatus.new.value,
        admin_note=None,
    )
    db.add(inquiry)
    await db.commit()
    await db.refresh(inquiry)
    return inquiry
