"""
Email Service — Handles drafting, immediate sending, scheduling, and cancellation of emails.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from app.models.scheduled_message import ScheduledMessage
from app.utils.notification_helper import send_email
from app.utils.llm import get_llm, invoke_llm_with_fallback
from langchain_core.messages import SystemMessage, HumanMessage
import json
import re
import logging

logger = logging.getLogger(__name__)


async def draft_email(
    instructions: str,
    recipient_name: Optional[str] = None,
    subject_hint: Optional[str] = None
) -> Tuple[str, str]:
    """
    Uses LLM to craft a polite, professional email subject and body
    based on user's natural language instructions.
    """
    recipient_label = recipient_name or "the recipient"
    prompt = (
        "You are an executive email assistant drafting an email on behalf of Vivek.\n"
        f"Recipient: {recipient_label}\n"
        f"Subject Hint: {subject_hint or 'None'}\n"
        f"User Instructions: {instructions}\n\n"
        "Draft a clean, polite, professional email.\n"
        "Respond ONLY with a JSON object in this exact format:\n"
        "{\n"
        '  "subject": "Clear, relevant subject line",\n'
        '  "body": "Formatted email body text with proper salutation and sign-off (Best regards,\\nVivek)"\n'
        "}"
    )

    try:
        messages = [
            SystemMessage(content="You are an expert executive email copywriter. Always output valid JSON."),
            HumanMessage(content=prompt)
        ]
        res = await invoke_llm_with_fallback(messages)
        content = res.content.strip()
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            subject = data.get("subject") or subject_hint or "Update from Vivek"
            body = data.get("body") or instructions
            return subject, body
    except Exception as e:
        logger.warning(f"LLM email drafting fallback due to: {e}")

    # Fallback formatting
    subj = subject_hint or "Update from Vivek"
    salutation = f"Hi {recipient_name},\n\n" if recipient_name else "Hello,\n\n"
    body = f"{salutation}{instructions}\n\nBest regards,\nVivek"
    return subj, body


async def send_immediate_email(to: str, subject: str, body: str) -> Dict[str, Any]:
    """Sends an email immediately via SMTP."""
    return await send_email(to=to, subject=subject, body=body)


async def schedule_email(
    db: AsyncSession,
    user_id: UUID,
    recipient: str,
    subject: str,
    message: str,
    scheduled_at: datetime,
    recipient_name: Optional[str] = None
) -> ScheduledMessage:
    """Saves an email to be sent at scheduled_at time."""
    new_msg = ScheduledMessage(
        user_id=user_id,
        recipient=recipient.strip(),
        recipient_name=recipient_name,
        subject=subject.strip(),
        message=message,
        scheduled_at=scheduled_at,
        channel="email",
        status="pending"
    )
    db.add(new_msg)
    await db.commit()
    await db.refresh(new_msg)
    logger.info(f"Scheduled email {new_msg.id} for {recipient} at {scheduled_at}")
    return new_msg


async def list_scheduled_emails(
    db: AsyncSession,
    user_id: UUID,
    status: Optional[str] = "pending"
) -> List[Dict[str, Any]]:
    """Lists scheduled emails for the current user."""
    stmt = select(ScheduledMessage).filter(
        ScheduledMessage.user_id == user_id,
        ScheduledMessage.channel == "email"
    )
    if status:
        stmt = stmt.filter(ScheduledMessage.status == status)
    stmt = stmt.order_by(ScheduledMessage.scheduled_at.asc())

    result = await db.execute(stmt)
    records = result.scalars().all()
    output = []
    for r in records:
        output.append({
            "id": str(r.id),
            "recipient": r.recipient,
            "recipient_name": r.recipient_name,
            "subject": r.subject,
            "message": r.message,
            "scheduled_at": r.scheduled_at.isoformat() if r.scheduled_at else None,
            "status": r.status,
            "sent_at": r.sent_at.isoformat() if r.sent_at else None,
            "error_message": r.error_message
        })
    return output


async def cancel_scheduled_email(
    db: AsyncSession,
    user_id: UUID,
    identifier: str
) -> Dict[str, Any]:
    """Cancels a scheduled email by UUID, recipient, or subject match."""
    if not identifier:
        return {"success": False, "message": "Please specify which scheduled email to cancel."}

    cleaned = identifier.strip()
    stmt = select(ScheduledMessage).filter(
        ScheduledMessage.user_id == user_id,
        ScheduledMessage.channel == "email",
        ScheduledMessage.status == "pending"
    )

    matched = None
    try:
        val_uuid = UUID(cleaned)
        stmt_uuid = stmt.filter(ScheduledMessage.id == val_uuid)
        res = await db.execute(stmt_uuid)
        matched = res.scalars().first()
    except ValueError:
        pass

    if not matched:
        stmt_text = stmt.filter(
            (ScheduledMessage.recipient.ilike(f"%{cleaned}%")) |
            (ScheduledMessage.recipient_name.ilike(f"%{cleaned}%")) |
            (ScheduledMessage.subject.ilike(f"%{cleaned}%"))
        ).order_by(desc(ScheduledMessage.created_at))
        res = await db.execute(stmt_text)
        matched = res.scalars().first()

    if matched:
        matched.status = "cancelled"
        await db.commit()
        return {
            "success": True,
            "message": f"Cancelled scheduled email to {matched.recipient_name or matched.recipient}: '{matched.subject or matched.message[:40]}'"
        }

    return {"success": False, "message": f"No active scheduled email found matching '{identifier}'."}
