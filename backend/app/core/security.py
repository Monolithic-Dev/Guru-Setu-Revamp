"""Password hashing and JWT helpers (security.md section 2, SEC-20).

bcrypt is used directly (cost 12). bcrypt only reads the first 72 bytes, so longer passwords are rejected rather
than silently truncated. Tokens are HS256 JWTs with {sub, role, iat, exp}; the role claim is informational only,
`api/deps.py` re-reads the role from the database on every request.
"""
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import get_settings
from app.core.errors import ApiError

BCRYPT_COST = 12
MAX_PASSWORD_BYTES = 72
ALGORITHM = "HS256"

# Verified against when the email is unknown, so login takes the same time either way (SEC-20).
# Hash of a random throwaway string; it matches no real password.
DUMMY_HASH = "$2b$12$4vyIh5dY9T2Txr9n6N6PB.nd6aiVPo8NCchzojpTV2u1F3xrZNEq6"


def password_too_long(plain: str) -> bool:
    return len(plain.encode("utf-8")) > MAX_PASSWORD_BYTES


def hash_password(plain: str) -> str:
    if password_too_long(plain):
        raise ValueError("Password is longer than 72 bytes (bcrypt limit).")
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(BCRYPT_COST)).decode("ascii")


def verify_password(plain: str, hashed: str) -> bool:
    """True only for a correct password. Never raises on bad input."""
    if password_too_long(plain):
        return False
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("ascii"))
    except ValueError:  # malformed hash
        return False


def create_token(sub: str, role: str) -> tuple[str, datetime]:
    """Return (jwt, expires_at in UTC)."""
    settings = get_settings()
    issued = datetime.now(UTC)
    expires = issued + timedelta(minutes=settings.jwt_expire_minutes)
    claims = {"sub": sub, "role": role, "iat": int(issued.timestamp()), "exp": int(expires.timestamp())}
    return jwt.encode(claims, settings.jwt_secret_key, algorithm=ALGORITHM), expires


def decode_token(token: str) -> dict:
    """Validate signature and expiry. Raises ApiError 401 (TOKEN_EXPIRED or UNAUTHENTICATED)."""
    try:
        return jwt.decode(
            token,
            get_settings().jwt_secret_key,
            algorithms=[ALGORITHM],  # never trust the header's alg
            options={"require": ["sub", "exp", "iat"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise ApiError("TOKEN_EXPIRED", 401, "Your session has expired. Please log in again.") from exc
    except jwt.PyJWTError as exc:
        raise ApiError("UNAUTHENTICATED", 401, "Missing or invalid token.") from exc
