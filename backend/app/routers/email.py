from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
import dateutil.parser

from app.database import get_db
from app.models.user import User
from app.utils.auth_helper import get_current_user
from app.services import email_service
from app.utils.timezone_helper import localize_to_utc

router = APIRouter(prefix="/email", tags=["Email"])


class SendEmailRequest(BaseModel):
    to: str = Field(..., min_length=3)
    subject: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)


class ScheduleEmailRequest(BaseModel):
    recipient: str = Field(..., min_length=3)
    recipient_name: Optional[str] = None
    subject: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    scheduled_at: str  # ISO datetime string or parseable time
    timezone_offset: Optional[int] = None


@router.post("/send")
async def send_email_direct(
    payload: SendEmailRequest,
    current_user: User = Depends(get_current_user)
):
    """Directly send an email via configured SMTP."""
    res = await email_service.send_immediate_email(
        to=payload.to,
        subject=payload.subject,
        body=payload.body
    )
    if not res.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res.get("error") or "Failed to send email"
        )
    return res


@router.post("/schedule")
async def schedule_email(
    payload: ScheduleEmailRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Schedule an email for future delivery."""
    try:
        parsed_dt = dateutil.parser.parse(payload.scheduled_at)
        scheduled_utc = localize_to_utc(parsed_dt, payload.timezone_offset)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scheduled_at datetime format: {str(e)}"
        )

    scheduled = await email_service.schedule_email(
        db=db,
        user_id=current_user.id,
        recipient=payload.recipient,
        subject=payload.subject,
        message=payload.message,
        scheduled_at=scheduled_utc,
        recipient_name=payload.recipient_name
    )

    return {
        "id": str(scheduled.id),
        "recipient": scheduled.recipient,
        "recipient_name": scheduled.recipient_name,
        "subject": scheduled.subject,
        "message": scheduled.message,
        "scheduled_at": scheduled.scheduled_at.isoformat(),
        "status": scheduled.status
    }


@router.get("/scheduled")
async def list_scheduled_emails(
    status_filter: Optional[str] = "pending",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List scheduled emails for the current user."""
    return await email_service.list_scheduled_emails(db, current_user.id, status_filter)


@router.delete("/scheduled/{message_id}")
async def cancel_scheduled_email(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel a pending scheduled email."""
    res = await email_service.cancel_scheduled_email(db, current_user.id, message_id)
    if not res.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=res.get("message")
        )
    return res
