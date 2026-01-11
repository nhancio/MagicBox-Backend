"""
Time utilities for consistent datetime handling across the application.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
import pytz


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def to_utc(dt: datetime) -> datetime:
    """Convert datetime to UTC if it's timezone-aware, otherwise assume UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def from_timestamp(ts: float) -> datetime:
    """Convert Unix timestamp to UTC datetime."""
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def to_timestamp(dt: datetime) -> float:
    """Convert UTC datetime to Unix timestamp."""
    return to_utc(dt).timestamp()


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S UTC") -> str:
    """Format datetime as string."""
    return to_utc(dt).strftime(format_str)


def parse_datetime(date_str: str, format_str: Optional[str] = None) -> datetime:
    """Parse datetime string to UTC datetime."""
    if format_str:
        dt = datetime.strptime(date_str, format_str)
    else:
        # Try ISO format first
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            # Fallback to common formats
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(f"Unable to parse datetime: {date_str}")
    
    return to_utc(dt)


def add_days(dt: datetime, days: int) -> datetime:
    """Add days to datetime."""
    return to_utc(dt) + timedelta(days=days)


def add_hours(dt: datetime, hours: int) -> datetime:
    """Add hours to datetime."""
    return to_utc(dt) + timedelta(hours=hours)


def add_minutes(dt: datetime, minutes: int) -> datetime:
    """Add minutes to datetime."""
    return to_utc(dt) + timedelta(minutes=minutes)


def is_expired(dt: datetime, expiry_seconds: Optional[int] = None) -> bool:
    """Check if datetime is expired (in the past)."""
    if expiry_seconds:
        return utc_now() > (to_utc(dt) + timedelta(seconds=expiry_seconds))
    return utc_now() > to_utc(dt)


def time_ago(dt: datetime) -> str:
    """Get human-readable time ago string."""
    delta = utc_now() - to_utc(dt)
    
    if delta.days > 365:
        years = delta.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif delta.days > 30:
        months = delta.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif delta.days > 0:
        return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
    elif delta.seconds > 3600:
        hours = delta.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif delta.seconds > 60:
        minutes = delta.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "just now"
