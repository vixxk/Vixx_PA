import asyncio
from datetime import datetime, timezone
from sqlalchemy.future import select
from app.database import AsyncSessionLocal
from app.models.reminder import Reminder
from app.models.scheduled_message import ScheduledMessage
from app.utils.notification_helper import send_email, send_sms, send_whatsapp
from app.utils.green_api_helper import send_whatsapp_message
from app.config import settings
import logging

logger = logging.getLogger(__name__)


async def start_reminder_daemon():
    """Background loop that checks for due reminders and scheduled messages every 10 seconds."""
    logger.info("🔔 Reminder & Message daemon started — checking every 10s for due items.")
    while True:
        try:
            await process_due_reminders()
            await process_due_scheduled_messages()
        except Exception as e:
            logger.error(f"Daemon background error: {e}")
        await asyncio.sleep(10)


async def process_due_scheduled_messages():
    """Processes pending scheduled WhatsApp messages whose scheduled_at is past or now."""
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        stmt = select(ScheduledMessage).filter(
            ScheduledMessage.status == "pending",
            ScheduledMessage.scheduled_at <= now
        )
        result = await db.execute(stmt)
        scheduled_msgs = result.scalars().all()

        for idx, sm in enumerate(scheduled_msgs, 1):
            ch = (sm.channel or "whatsapp").lower()
            logger.info(f"Processing scheduled {ch} {idx}/{len(scheduled_msgs)} to {sm.recipient}")
            try:
                if ch == "email":
                    subj = sm.subject or "Update from Vivek"
                    res = await send_email(to=sm.recipient, subject=subj, body=sm.message)
                else:  # whatsapp
                    res = await send_whatsapp_message(sm.recipient, sm.message)

                if res.get("success"):
                    sm.status = "sent"
                    sm.sent_at = now
                    sm.error_message = None
                    logger.info(f"✅ Scheduled {ch} {sm.id} successfully sent to {sm.recipient}.")
                else:
                    sm.status = "failed"
                    sm.error_message = str(res.get("error") or "Unknown error")
                    logger.error(f"❌ Scheduled {ch} {sm.id} failed: {sm.error_message}")
            except Exception as ex:
                sm.status = "failed"
                sm.error_message = str(ex)
                logger.error(f"❌ Scheduled {ch} {sm.id} exception: {ex}")

        if scheduled_msgs:
            await db.commit()
            logger.info(f"✅ Processed {len(scheduled_msgs)} due scheduled message(s).")


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
            
            # Message formatting
            alert_body = f"🚨 *VIXX ALERT*\n\n📌 *Task*: {reminder.title}"
            if reminder.description:
                alert_body += f"\n📝 *Detail*: {reminder.description}"
            alert_body += f"\n\n⏰ *Time*: {local_remind_at.strftime('%b %d, %Y at %I:%M %p')}"

            email_body = f"⏰ *VIXX REMINDER*: {reminder.title}"
            if reminder.description:
                email_body += f"\n📝 {reminder.description}"
            email_body += f"\n🕐 Scheduled: {local_remind_at.strftime('%b %d, %Y at %I:%M %p')}"

            success = False
            channel = (reminder.channel or "sms").lower()

            # WhatsApp channel
            if channel in ("whatsapp", "all"):
                wa_recipient = settings.DEFAULT_WHATSAPP_NUMBER or settings.USER_SMS_NUMBER
                res = await send_whatsapp(wa_recipient, alert_body)
                if res.get("success"):
                    success = True
                    logger.info(f"WhatsApp alert sent: {reminder.title}")

            # SMS channel
            if channel in ("sms", "both", "all"):
                to_number = settings.USER_SMS_NUMBER
                res = await send_sms(to_number, alert_body)
                if res.get("success"):
                    success = True
                    logger.info(f"SMS alert sent: {reminder.title}")

            # Email channel
            if channel in ("email", "both", "all"):
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
