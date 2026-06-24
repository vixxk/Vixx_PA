import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger(__name__)


from typing import List, Optional

async def send_whatsapp(to: str, body: str, template_params: Optional[List[str]] = None, button_url: Optional[str] = None) -> dict:
    """Send a WhatsApp message via Meta Cloud API."""
    from app.config import settings
    import httpx

    meta_token = settings.META_WHATSAPP_ACCESS_TOKEN
    meta_phone_id = settings.META_WHATSAPP_PHONE_NUMBER_ID
    meta_version = settings.META_WHATSAPP_VERSION or "v20.0"

    if not meta_token or not meta_phone_id:
        logger.warning("Meta WhatsApp credentials not set — logging WhatsApp message locally.")
        print(f"\n📱 [WHATSAPP LOCAL LOG] To: {to}\n   Message: {body}\n")
        _log_notification("whatsapp", to, body)
        return {"success": True, "mode": "local_log"}

    # Format recipient number for Meta API (strip 'whatsapp:' prefix and keep only digits)
    clean_to = to
    if clean_to.lower().startswith("whatsapp:"):
        clean_to = clean_to[9:]
    clean_to = "".join(c for c in clean_to if c.isdigit())
    # Note: Meta API expects recipient phone number with country code but NO '+' prefix (e.g. 917352648994)

    template_name = getattr(settings, "META_WHATSAPP_TEMPLATE_NAME", "")
    template_lang = getattr(settings, "META_WHATSAPP_TEMPLATE_LANG", "en_US") or "en_US"

    try:
        url = f"https://graph.facebook.com/{meta_version}/{meta_phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {meta_token}",
            "Content-Type": "application/json"
        }
        
        if template_name:
            # Map template_params if provided, otherwise clean the single body string
            params = []
            if template_params:
                for param in template_params:
                    cleaned_param = str(param).replace("\n", " ").replace("\r", "").replace("\t", " ")
                    while "     " in cleaned_param:
                        cleaned_param = cleaned_param.replace("     ", "    ")
                    params.append({"type": "text", "text": cleaned_param})
            else:
                # Meta template parameters do not allow newlines, carriage returns, tabs, or >4 consecutive spaces
                cleaned_body = body.replace("\n", " | ").replace("\r", "").replace("\t", " ")
                while "     " in cleaned_body:
                    cleaned_body = cleaned_body.replace("     ", "    ")
                params.append({"type": "text", "text": cleaned_body})
                
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": clean_to,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": template_lang
                    },
                    "components": [
                        {
                            "type": "body",
                            "parameters": params
                        }
                    ]
                }
            }
            
            # Append dynamic URL button component if button_url is supplied
            if button_url:
                clean_button_param = button_url.strip()
                if clean_button_param.startswith("https://"):
                    clean_button_param = clean_button_param[8:]
                elif clean_button_param.startswith("http://"):
                    clean_button_param = clean_button_param[7:]
                
                payload["template"]["components"].append({
                    "type": "button",
                    "sub_type": "url",
                    "index": "0",
                    "parameters": [
                        {
                            "type": "text",
                            "text": clean_button_param
                        }
                    ]
                })
        else:
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": clean_to,
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body": body
                }
            }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code in (200, 201):
                logger.info(f"WhatsApp sent to {to} via Meta Cloud API.")
                return {"success": True, "mode": "meta", "message_id": resp.json().get("messages", [{}])[0].get("id")}
            
            # If Meta WhatsApp Token is expired or unauthorized, log locally to avoid blocking app use
            if resp.status_code == 401 or "OAuthException" in resp.text:
                logger.warning("Meta WhatsApp credentials expired or unauthorized (401) — falling back to local logging.")
                print(f"\n📱 [WHATSAPP LOCAL LOG (FALLBACK)] To: {to}\n   Message: {body}\n")
                _log_notification("whatsapp", to, body)
                return {"success": True, "mode": "local_log_fallback"}

            # Auto-fallback: If parameter/component mismatch occurs
            if resp.status_code == 400 and template_name and "components" in payload["template"]:
                resp_text = resp.text
                if any(x in resp_text for x in ("132000", "100", "component", "button", "parameter")):
                    # Level 1: Retry without the button component (if present)
                    has_button = any(c.get("type") == "button" for c in payload["template"]["components"])
                    if has_button:
                        logger.warning("Component mismatch detected. Retrying without button component.")
                        payload["template"]["components"] = [
                            c for c in payload["template"]["components"]
                            if c.get("type") != "button"
                        ]
                        resp = await client.post(url, json=payload, headers=headers)
                        if resp.status_code in (200, 201):
                            logger.info(f"WhatsApp sent to {to} via Meta Cloud API (fallback without button).")
                            return {"success": True, "mode": "meta", "message_id": resp.json().get("messages", [{}])[0].get("id")}
                    
                    # Level 2: Retry without any components
                    if "components" in payload["template"]:
                        logger.warning("Parameter/component mismatch persists. Retrying without any components.")
                        payload["template"].pop("components")
                        resp = await client.post(url, json=payload, headers=headers)
                        if resp.status_code in (200, 201):
                            logger.info(f"WhatsApp sent to {to} via Meta Cloud API (fallback without components).")
                            return {"success": True, "mode": "meta", "message_id": resp.json().get("messages", [{}])[0].get("id")}
            
            logger.error(f"Meta API error {resp.status_code}: {resp.text}")
            return {"success": False, "error": resp.text}
    except Exception as e:
        logger.error(f"Meta WhatsApp send failed: {e}")
        _log_notification("whatsapp", to, body)
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
