"""
Token encryption utilities (Fernet).

Used for encrypting OAuth tokens at rest in Postgres.
In production, set ENCRYPTION_KEY in backend/.env (Fernet key).

Notes:
- Fernet provides authenticated encryption (AES128-CBC + HMAC).
- We keep a small compatibility shim: if a value doesn't look like a Fernet token,
  we treat it as plaintext (for existing dev DB rows).
"""

from __future__ import annotations

from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from app.config.settings import settings


def _get_fernet() -> Optional[Fernet]:
    if not settings.ENCRYPTION_KEY:
        return None
    return Fernet(settings.ENCRYPTION_KEY.encode("utf-8"))


def encrypt_token(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    f = _get_fernet()
    if not f:
        # dev fallback: store plaintext (not production-grade)
        return value
    return f.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_token(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    f = _get_fernet()
    if not f:
        return value

    # Compatibility: already-plaintext tokens from earlier dev runs
    if not value.startswith("gAAAA"):
        return value

    try:
        return f.decrypt(value.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        # If the key rotated or token isn't Fernet, return as-is to avoid hard crashes in dev.
        return value


class EncryptionService:
    """Service class wrapper for encryption utilities."""
    
    @staticmethod
    def encrypt(data: str) -> str:
        """Encrypt a string using Fernet."""
        result = encrypt_token(data)
        if result is None:
            return data
        return result
    
    @staticmethod
    def decrypt(encrypted_data: str) -> str:
        """Decrypt a string using Fernet."""
        result = decrypt_token(encrypted_data)
        if result is None:
            return encrypted_data
        return result
    
    @staticmethod
    def generate_key() -> str:
        """Generate a new Fernet key."""
        return Fernet.generate_key().decode("utf-8")

