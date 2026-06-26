import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger(__name__)




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
