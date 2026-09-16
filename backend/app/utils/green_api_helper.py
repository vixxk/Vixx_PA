import os
import re
import logging
from datetime import datetime
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


def format_whatsapp_chat_id(phone_or_chat_id: str) -> str:
    """
    Format a phone number or WhatsApp ID into the Green API chatId format:
    - For individual chats: '11001234567@c.us'
    - For group chats: '123456789-123456@g.us'
    """
    cleaned = (phone_or_chat_id or "").strip()
    if not cleaned:
        return ""

    # If already formatted with suffix
    if cleaned.endswith("@c.us") or cleaned.endswith("@g.us"):
        return cleaned

    # Strip any +, spaces, dashes, brackets
    digits = re.sub(r"\D", "", cleaned)
    if not digits:
        return ""

    # If standard 10-digit number without country code, prefix India (+91) as default
    if len(digits) == 10:
        digits = f"91{digits}"
    # If 11-digit number starting with 0, replace leading 0 with country code
    elif len(digits) == 11 and digits.startswith("0"):
        digits = f"91{digits[1:]}"

    return f"{digits}@c.us"


def get_green_api_credentials():
    """
    Resolves Green API credentials from settings or environment variables,
    supporting standard and alternate variable names.
    """
    instance_id = (
        settings.GREEN_API_INSTANCE_ID 
        or os.getenv("GREEN_API_INSTANCE_ID") 
        or os.getenv("GREEN_API_ID_INSTANCE") 
        or ""
    ).strip()

    api_token = (
        settings.GREEN_API_API_TOKEN_INSTANCE 
        or os.getenv("GREEN_API_API_TOKEN_INSTANCE") 
        or os.getenv("GREEN_API_TOKEN") 
        or os.getenv("GREEN_API_API_KEY") 
        or ""
    ).strip()

    host = (
        settings.GREEN_API_HOST 
        or os.getenv("GREEN_API_HOST") 
        or "https://api.green-api.com"
    ).strip().rstrip("/")

    return instance_id, api_token, host


def _log_whatsapp_locally(recipient: str, message: str, status: str = "LOGGED"):
    """Saves outgoing WhatsApp messages to a local log file for inspection and testing."""
    log_dir = "notification_logs"
    os.makedirs(log_dir, exist_ok=True)
    ts = datetime.utcnow().isoformat()
    with open(f"{log_dir}/sent_whatsapp.log", "a", encoding="utf-8") as f:
        f.write(f"[{ts}] [{status}] To: {recipient} | {message}\n")


async def send_whatsapp_message(to: str, message: str) -> dict:
    """
    Sends a WhatsApp message via Green API.
    If credentials are not yet configured in .env, cleanly logs locally without breaking execution.
    """
    instance_id, api_token, host = get_green_api_credentials()
    chat_id = format_whatsapp_chat_id(to)

    if not chat_id:
        return {"success": False, "error": "Invalid recipient phone number or WhatsApp ID."}

    # If credentials are not configured, fallback to local logging
    if not instance_id or not api_token:
        logger.warning("Green API credentials not configured in .env — logging WhatsApp message locally.")
        print(f"\n📲 [WHATSAPP LOCAL LOG] To: {chat_id}\n   Message: {message}\n")
        _log_whatsapp_locally(chat_id, message, status="LOCAL_LOG")
        return {
            "success": True,
            "mode": "local_log",
            "chatId": chat_id,
            "message": "Logged locally. Add GREEN_API_INSTANCE_ID and GREEN_API_API_TOKEN_INSTANCE to .env to send real WhatsApp messages."
        }

    url = f"{host}/waInstance{instance_id}/sendMessage/{api_token}"
    payload = {
        "chatId": chat_id,
        "message": message
    }

    try:
        logger.info(f"Green API sending WhatsApp message to {chat_id} via {host}...")
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(url, json=payload)
            logger.info(f"Green API response code: {resp.status_code}")

            if resp.status_code in (200, 201):
                data = resp.json()
                msg_id = data.get("idMessage")
                logger.info(f"✅ WhatsApp message delivered to {chat_id} (idMessage: {msg_id})")
                _log_whatsapp_locally(chat_id, message, status="SENT")
                return {
                    "success": True,
                    "mode": "green_api",
                    "idMessage": msg_id,
                    "chatId": chat_id
                }
            else:
                error_text = resp.text
                logger.error(f"❌ Green API error {resp.status_code}: {error_text}")
                _log_whatsapp_locally(chat_id, message, status=f"FAILED_{resp.status_code}")
                return {
                    "success": False,
                    "mode": "green_api",
                    "error": error_text,
                    "statusCode": resp.status_code,
                    "chatId": chat_id
                }
    except Exception as e:
        import traceback
        logger.error(f"❌ Green API exception: {e}\n{traceback.format_exc()}")
        _log_whatsapp_locally(chat_id, message, status=f"EXCEPTION_{str(e)}")
        return {
            "success": False,
            "mode": "green_api",
            "error": str(e),
            "chatId": chat_id
        }


async def check_green_api_status() -> dict:
    """Checks Green API instance connection state (e.g. authorized, notAuthorized)."""
    instance_id, api_token, host = get_green_api_credentials()
    if not instance_id or not api_token:
        return {
            "configured": False,
            "message": "Green API credentials not set in backend/.env"
        }

    url = f"{host}/waInstance{instance_id}/getStateInstance/{api_token}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "configured": True,
                    "status_code": resp.status_code,
                    "stateInstance": data.get("stateInstance"),
                    "host": host,
                    "instance_id": instance_id
                }
            return {
                "configured": True,
                "status_code": resp.status_code,
                "error": resp.text
            }
    except Exception as e:
        return {
            "configured": True,
            "error": str(e)
        }
