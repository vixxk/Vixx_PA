import time
from datetime import datetime, timezone, timedelta
from typing import Optional

def localize_to_utc(dt: datetime, tz_offset_minutes: Optional[int] = None) -> datetime:
    """
    Localizes a timezone-naive or timezone-aware datetime to UTC
    using the provided JavaScript style timezone offset (in minutes),
    or falling back to the server local timezone offset.
    """
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc)
        
    if tz_offset_minutes is not None:
        # JS getTimezoneOffset() returns negative minutes for positive UTC offsets.
        # e.g., IST (UTC+05:30) returns -330.
        # So user_offset = -(-330) = 330 minutes
        user_tz = timezone(timedelta(minutes=-tz_offset_minutes))
    else:
        # Fallback to server local timezone offset
        server_offset_seconds = -time.timezone if time.daylight == 0 else -time.altzone
        user_tz = timezone(timedelta(seconds=server_offset_seconds))
        
    localized_dt = dt.replace(tzinfo=user_tz)
    return localized_dt.astimezone(timezone.utc)
