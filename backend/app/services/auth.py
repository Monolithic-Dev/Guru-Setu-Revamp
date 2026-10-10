"""Login (API-001): equal-time credential check, same error for unknown email and wrong password (SEC-20)."""
from datetime import UTC

from app.core.config import get_settings
from app.core.database import run_read
from app.core.errors import ApiError
from app.core.ratelimit import RateLimiter
from app.core.security import DUMMY_HASH, create_token, password_too_long, verify_password
from app.repos import users_repo

_limiter: RateLimiter | None = None


def _login_limiter() -> RateLimiter:
    global _limiter
    if _limiter is None:
        _limiter = RateLimiter(get_settings().login_rate_limit_per_min, 60)
    return _limiter


def reset_login_limiter() -> None:
    """For tests."""
    if _limiter is not None:
        _limiter.reset()


def login(email: str, password: str, client_ip: str) -> dict:
    _login_limiter().check(client_ip)  # 429 with Retry-After beyond LOGIN_RATE_LIMIT_PER_MIN per IP

    record = run_read(users_repo.get_login_record, email=email.strip().lower())
    # Always run one bcrypt comparison so response time does not reveal whether the email exists.
    hashed = record["password_hash"] if record else DUMMY_HASH
    ok = verify_password(password, hashed) and record is not None
    if not ok:
        raise ApiError("INVALID_CREDENTIALS", 401, "Email or password is incorrect.")
    if password_too_long(password):  # defensive: verify_password already returns False for these
        raise ApiError("INVALID_CREDENTIALS", 401, "Email or password is incorrect.")

    token, expires = create_token(record["user_id"], record["role"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": record["role"],
        "user_id": record["user_id"],
        "expires_at": expires.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }
