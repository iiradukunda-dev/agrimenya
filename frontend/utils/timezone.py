import os
import time
from datetime import datetime

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # type: ignore

CAT_TIMEZONE = "Africa/Kigali"
CAT_TZ = ZoneInfo(CAT_TIMEZONE)

def setup_system_timezone():
    """
    Enforces Central Africa Time (CAT) UTC+2 as the default timezone 
    for the application environment.
    """
    os.environ['TZ'] = CAT_TIMEZONE
    tzset = getattr(time, 'tzset', None)
    if tzset:
        tzset()

def get_current_time() -> datetime:
    """Returns the current datetime explicitly in CAT (UTC+2)."""
    return datetime.now(CAT_TZ)

def to_cat(dt: datetime) -> datetime:
    """Converts any datetime to CAT timezone."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(CAT_TZ)
