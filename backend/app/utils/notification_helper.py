import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger(__name__)




async def send_sms(to: str, body: str) -> dict:
    """Send an SMS via Twilio Cloud API."""
    from app.config import settings
    import httpx

    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    from_number = settings.TWILIO_PHONE_NUMBER

    if not account_sid or not auth_token or not from_number:
        logger.warning("Twilio SMS credentials not set — logging SMS message locally.")
        print(f"\n📱 [SMS LOCAL LOG] To: {to}\n   Message: {body}\n")
        _log_notification("sms", to, body)
        return {"success": True, "mode": "local_log"}

    # Format phone number: ensure country code (e.g. +91...) is present
    clean_to = to.strip()
    if not clean_to.startswith("+"):
        # Default to India (+91) if 10-digit number without country code
        digits_only = "".join(c for c in clean_to if c.isdigit())
        if len(digits_only) == 10:
            clean_to = f"+91{digits_only}"
        else:
            clean_to = f"+{digits_only}"

    try:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
        auth = (account_sid, auth_token)
        payload = {
            "To": clean_to,
            "From": from_number,
            "Body": body
        }
        logger.info(f"SMS send attempt — to: {clean_to} (from: {from_number})")
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, data=payload, auth=auth)
            logger.info(f"Twilio API response — status: {resp.status_code}")
            if resp.status_code in (200, 201):
                msg_sid = resp.json().get("sid")
                logger.info(f"✅ SMS sent to {clean_to} via Twilio (sid: {msg_sid}).")
                return {"success": True, "mode": "twilio", "message_id": msg_sid}
            else:
                logger.error(f"❌ Twilio API error {resp.status_code}: {resp.text}")
                _log_notification("sms", to, body)
                return {"success": False, "error": resp.text}
    except Exception as e:
        import traceback
        logger.error(f"❌ Twilio SMS send failed: {e}\n{traceback.format_exc()}")
        _log_notification("sms", to, body)
        return {"success": False, "error": str(e)}


async def send_email(to: str, subject: str, body: str) -> dict:
    """Send an email via SMTP if configured, otherwise log locally."""
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if smtp_server and smtp_user and smtp_password:
        try:
            port = int(smtp_port) if smtp_port else 587
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = to
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(smtp_server, port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, to, msg.as_string())
            server.quit()
            logger.info(f"Email sent to {to}")
            return {"success": True, "mode": "smtp"}
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return {"success": False, "error": str(e)}
    else:
        logger.warning("SMTP not configured — logging email locally.")
        print(f"\n📧 [EMAIL LOCAL LOG] To: {to}\n   Subject: {subject}\n   Body: {body}\n")
        _log_notification("email", to, f"{subject}: {body}")
        return {"success": True, "mode": "local_log"}


def _log_notification(channel: str, recipient: str, message: str):
    log_dir = "notification_logs"
    os.makedirs(log_dir, exist_ok=True)
    from datetime import datetime
    ts = datetime.utcnow().isoformat()
    with open(f"{log_dir}/sent_reminders.log", "a") as f:
        f.write(f"[{ts}] [{channel.upper()}] To: {recipient} | {message}\n")
