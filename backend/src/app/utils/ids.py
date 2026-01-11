"""
ID generation utilities for consistent ID formats across the application.
"""
import uuid
import secrets
import string
from typing import Optional


def generate_uuid() -> str:
    """Generate a standard UUID v4 string."""
    return str(uuid.uuid4())


def generate_short_id(length: int = 12) -> str:
    """Generate a short, URL-safe random ID."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_numeric_id(length: int = 10) -> str:
    """Generate a numeric ID."""
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def generate_slug_id(prefix: Optional[str] = None, length: int = 8) -> str:
    """Generate a slug-like ID with optional prefix."""
    alphabet = string.ascii_lowercase + string.digits
    suffix = ''.join(secrets.choice(alphabet) for _ in range(length))
    if prefix:
        return f"{prefix}-{suffix}"
    return suffix


def is_valid_uuid(uuid_string: str) -> bool:
    """Check if a string is a valid UUID."""
    try:
        uuid.UUID(uuid_string)
        return True
    except (ValueError, AttributeError):
        return False


def normalize_id(id_string: str) -> str:
    """Normalize an ID string (lowercase, strip whitespace)."""
    return id_string.strip().lower() if id_string else ""