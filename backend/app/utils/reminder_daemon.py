import asyncio
from datetime import datetime, timezone
from sqlalchemy.future import select
from app.database import AsyncSessionLocal
from app.models.reminder import Reminder
from app.utils.notification_helper import send_whatsapp, send_email
from app.config import settings
import logging

logger = logging.getLogger(__name__)


async def start_reminder_daemon():
    """Background loop that checks for due reminders every 10 seconds and sends notifications."""
    logger.info("🔔 Reminder daemon started — checking every 10s for due reminders.")
    while True:
        try:
            await process_due_reminders()
        except Exception as e:
            logger.error(f"Reminder daemon error: {e}")
        await asyncio.sleep(10)


async def process_due_reminders():
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)

        stmt = select(Reminder).filter(
            Reminder.status == "pending",
            Reminder.remind_at <= now
        )
        result = await db.execute(stmt)
        reminders = result.scalars().all()

        for reminder in reminders:
            body = f"⏰ *REMINDER*: {reminder.title}"
            if reminder.description:
                body += f"\n📝 {reminder.description}"
            # Convert UTC stored datetime to local timezone for readability
            local_remind_at = reminder.remind_at.astimezone()
            body += f"\n🕐 Scheduled: {local_remind_at.strftime('%b %d, %Y at %I:%M %p')}"

            success = False
            channel = reminder.channel or "whatsapp"

            if channel in ("whatsapp", "both"):
                to_number = settings.USER_WHATSAPP_NUMBER
                
                # Format parameters for specific template layouts
                template_params = None
                template_name = getattr(settings, "META_WHATSAPP_TEMPLATE_NAME", "")
                
                if template_name in ("reminder_alert", "reminder"):
                    local_remind_at = reminder.remind_at.astimezone()
                    due_date_str = local_remind_at.strftime('%b %d, %Y at %I:%M %p')
                    template_params = [reminder.title, due_date_str]
                elif template_name in ("reminder_task", "templated"):
                    local_remind_at = reminder.remind_at.astimezone()
                    due_date_str = local_remind_at.strftime('%b %d, %Y at %I:%M %p')
                    template_params = [
                        reminder.title,
                        reminder.description or "No description provided",
                        due_date_str
                    ]
                elif template_name == "jaspers_market_order_confirmation_v1":
                    local_remind_at = reminder.remind_at.astimezone()
                    due_date_str = local_remind_at.strftime('%b %d, %Y at %I:%M %p')
                    template_params = ["Vixx! ⏰ REMINDER", reminder.title, due_date_str]
                    
                import re
                url_match = re.search(r'(https?://\S+)', reminder.description or '')
                if not url_match:
                    url_match = re.search(r'(https?://\S+)', reminder.title or '')
                button_url = url_match.group(1) if url_match else None
                    
                res = await send_whatsapp(to_number, body, template_params=template_params, button_url=button_url)
                if res.get("success"):
                    success = True
                    logger.info(f"WhatsApp reminder sent: {reminder.title}")

            if channel in ("email", "both"):
                # Get user email from relationship
                from app.models.user import User
                user_stmt = select(User).filter(User.id == reminder.user_id)
                user_res = await db.execute(user_stmt)
                user = user_res.scalars().first()
                if user:
                    import os
                    recipient_email = os.getenv("SMTP_USER") or user.email
                    res = await send_email(recipient_email, f"Reminder: {reminder.title}", body)
                    if res.get("success"):
                        success = True

            reminder.status = "sent" if success else "failed"
            reminder.sent_at = now

        if reminders:
            await db.commit()
            logger.info(f"Processed {len(reminders)} due reminder(s).")
