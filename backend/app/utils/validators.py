"""
Input Validators — Production hardening for all user-provided data.
"""
import re
from datetime import datetime
from typing import Tuple, Optional


def validate_payment_amount(amount) -> Tuple[bool, str]:
    """Validate payment amounts."""
    if amount is None:
        return False, "Payment amount is required."
    try:
        amt = float(amount)
    except (ValueError, TypeError):
        return False, f"Invalid amount '{amount}'. Must be a number."
    if amt <= 0:
        return False, "Payment amount must be greater than zero."
    if amt > 100_000_000:
        return False, "Payment amount seems unreasonably large. Please verify."
    return True, ""


def validate_date(date_str, allow_future=True, allow_past=True) -> Tuple[bool, str]:
    """Validate date strings."""
    if not date_str:
        return True, ""  # Optional dates are ok
    try:
        import dateutil.parser
        dt = dateutil.parser.parse(str(date_str))
        if not allow_future and dt > datetime.now():
            return False, "Future dates are not allowed for this field."
        if not allow_past and dt < datetime.now():
            return False, "Past dates are not allowed for this field."
        return True, ""
    except Exception:
        return False, f"Could not parse date '{date_str}'. Use format YYYY-MM-DD."


def validate_project_title(title) -> Tuple[bool, str]:
    """Validate project titles."""
    if not title or not str(title).strip():
        return False, "Project title is required."
    title = str(title).strip()
    if len(title) > 255:
        return False, "Project title is too long (max 255 characters)."
    if len(title) < 2:
        return False, "Project title is too short (min 2 characters)."
    return True, ""


VALID_CURRENCIES = {"INR", "USD", "EUR", "GBP", "AUD", "CAD", "JPY", "CNY", "SGD", "AED", "CHF", "NZD", "BTC", "ETH"}

def validate_currency(currency) -> Tuple[bool, str]:
    """Validate ISO 4217 currency codes."""
    if not currency:
        return True, ""  # Default will be applied
    cur = str(currency).upper().strip()
    if cur not in VALID_CURRENCIES:
        return False, f"Unknown currency '{currency}'. Supported: {', '.join(sorted(VALID_CURRENCIES))}."
    return True, ""


def sanitize_string(value: str, max_length: int = 500) -> str:
    """Sanitize user-provided strings: strip, truncate, remove control chars."""
    if not value:
        return value
    # Remove control characters except newline/tab
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', str(value))
    return cleaned.strip()[:max_length]
