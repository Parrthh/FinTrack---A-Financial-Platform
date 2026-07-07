"""Password hashing and token issuance.

- Passwords: bcrypt (never logged, never stored in reversible form).
- Access tokens: short-lived JWTs signed with JWT_SECRET.
- Refresh tokens: opaque random strings; only a SHA-256 hash is stored so a
  DB leak can't be replayed as a live session.
"""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.config import get_settings

settings = get_settings()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        return False


def create_access_token(user_id: uuid.UUID) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(seconds=settings.access_token_ttl_seconds),
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> uuid.UUID | None:
    """Return the user id for a valid access token, else None."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.InvalidTokenError:
        return None
    if payload.get("type") != "access":
        return None
    try:
        return uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        return None


def generate_refresh_token() -> tuple[str, str, datetime]:
    """Return (raw_token, token_hash, expires_at). Only the hash is persisted."""
    raw = secrets.token_urlsafe(48)
    token_hash = hash_refresh_token(raw)
    expires_at = datetime.now(UTC) + timedelta(
        seconds=settings.refresh_token_ttl_seconds
    )
    return raw, token_hash, expires_at


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()
