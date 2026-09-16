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
from app.utils.green_api_helper import check_green_api_status
from app.services import whatsapp_service
from app.utils.timezone_helper import localize_to_utc

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])


class SendWhatsAppRequest(BaseModel):
    recipient: Optional[str] = None
    message: str = Field(..., min_length=1)


class ScheduleWhatsAppRequest(BaseModel):
    recipient: Optional[str] = None
    recipient_name: Optional[str] = None
    message: str = Field(..., min_length=1)
    scheduled_at: str  # ISO datetime string or parseable time
    timezone_offset: Optional[int] = None


@router.get("/status")
async def get_whatsapp_status(
    current_user: User = Depends(get_current_user)
):
    """Check Green API configuration and connection status."""
    return await check_green_api_status()


@router.post("/send")
async def send_whatsapp_direct(
    payload: SendWhatsAppRequest,
    current_user: User = Depends(get_current_user)
):
    """Directly send a WhatsApp message via Green API."""
    res = await whatsapp_service.send_immediate(payload.recipient, payload.message)
    if not res.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res.get("error") or "Failed to send WhatsApp message"
        )
    return res


@router.post("/schedule")
async def schedule_whatsapp(
    payload: ScheduleWhatsAppRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Schedule a WhatsApp message for future delivery."""
    try:
        parsed_dt = dateutil.parser.parse(payload.scheduled_at)
        scheduled_utc = localize_to_utc(parsed_dt, payload.timezone_offset)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scheduled_at datetime format: {str(e)}"
        )

    scheduled = await whatsapp_service.schedule_message(
        db=db,
        user_id=current_user.id,
        recipient=payload.recipient,
        message=payload.message,
        scheduled_at=scheduled_utc,
        recipient_name=payload.recipient_name
    )

    return {
        "id": str(scheduled.id),
        "recipient": scheduled.recipient,
        "recipient_name": scheduled.recipient_name,
        "message": scheduled.message,
        "scheduled_at": scheduled.scheduled_at.isoformat(),
        "status": scheduled.status
    }


@router.get("/scheduled")
async def list_scheduled_whatsapp(
    status_filter: Optional[str] = "pending",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List scheduled WhatsApp messages for the current user."""
    return await whatsapp_service.list_scheduled_messages(db, current_user.id, status_filter)


@router.delete("/scheduled/{message_id}")
async def cancel_scheduled_whatsapp(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel a pending scheduled WhatsApp message."""
    res = await whatsapp_service.cancel_scheduled_message(db, current_user.id, message_id)
    if not res.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=res.get("message")
        )
    return res
