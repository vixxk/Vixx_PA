import asyncio
from datetime import datetime, timezone
from sqlalchemy.future import select
from app.database import AsyncSessionLocal
from app.models.reminder import Reminder
from app.utils.notification_helper import send_email, send_sms
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

        for idx, reminder in enumerate(reminders, 1):
            logger.info(f"Processing reminder {idx}/{len(reminders)}: '{reminder.title}' (channel={reminder.channel})")
            
            local_remind_at = reminder.remind_at.astimezone()
            
            # Premium SMS Alert Template
            sms_body = f"🚨 *VIXX ALERT*\n\n📌 *Task*: {reminder.title}"
            if reminder.description:
                sms_body += f"\n📝 *Detail*: {reminder.description}"
            sms_body += f"\n\n⏰ *Time*: {local_remind_at.strftime('%b %d, %Y at %I:%M %p')}"

            # Email Body Template
            email_body = f"⏰ *VIXX REMINDER*: {reminder.title}"
            if reminder.description:
                email_body += f"\n📝 {reminder.description}"
            email_body += f"\n🕐 Scheduled: {local_remind_at.strftime('%b %d, %Y at %I:%M %p')}"

            success = False
            channel = reminder.channel or "sms"

            if channel in ("sms", "both"):
                to_number = settings.USER_SMS_NUMBER
                res = await send_sms(to_number, sms_body)
                if res.get("success"):
                    success = True
                    logger.info(f"SMS alert sent: {reminder.title}")

            if channel in ("email", "both"):
                # Get user email from relationship
                from app.models.user import User
                user_stmt = select(User).filter(User.id == reminder.user_id)
                user_res = await db.execute(user_stmt)
                user = user_res.scalars().first()
                if user:
                    import os
                    recipient_email = os.getenv("SMTP_USER") or user.email
                    res = await send_email(recipient_email, f"Vixx Reminder: {reminder.title}", email_body)
                    if res.get("success"):
                        success = True

            reminder.status = "sent" if success else "failed"
            reminder.sent_at = now
            logger.info(f"Reminder '{reminder.title}' marked as {reminder.status}")

        if reminders:
            await db.commit()
            logger.info(f"✅ Processed {len(reminders)} due reminder(s).")
