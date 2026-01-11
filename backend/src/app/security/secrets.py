"""
Secrets helper utilities.

Goals:
- Centralize reading of secrets from env/settings.
- Provide safe redaction for logs.
- Provide Fernet key generation helper (for ENCRYPTION_KEY).
"""

from __future__ import annotations

import base64
import os
from typing import Optional

from cryptography.fernet import Fernet

from app.config.settings import settings


def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    return os.environ.get(name, default)


def redact(value: Optional[str], keep: int = 4) -> str:
    if not value:
        return ""
    if len(value) <= keep:
        return "*" * len(value)
    return value[:keep] + "…" + "*" * 6


def get_encryption_key() -> Optional[str]:
    """
    Returns the Fernet key used for token encryption, or None in dev if unset.
    """
    return settings.ENCRYPTION_KEY or None


def generate_fernet_key() -> str:
    """
    Generate a new Fernet key (urlsafe base64). Store it in backend/.env as ENCRYPTION_KEY.
    """
    return Fernet.generate_key().decode("utf-8")


