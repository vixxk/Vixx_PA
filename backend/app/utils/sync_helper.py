import logging

logger = logging.getLogger(__name__)

async def trigger_payments_sheet_sync(db, user_id: str, google_token: str):
    # Google Sheets integration has been disabled
    return {"success": True, "message": "Google Sheets integration is disabled."}
