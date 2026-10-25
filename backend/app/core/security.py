"""Password hashing (bcrypt) and JWT helpers."""
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import Settings

ALGORITHM = "HS256"


def hash_password(password: str, rounds: int = 12) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=rounds)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user_id: str, settings: Settings) -> tuple[str, str, datetime]:
    """Returns (token, jti, expires_at)."""
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=settings.access_token_expire_minutes)
    jti = uuid.uuid4().hex
    token = jwt.encode(
        {"sub": user_id, "jti": jti, "iat": int(now.timestamp()), "exp": int(expires.timestamp())},
        settings.secret_key,
        algorithm=ALGORITHM,
    )
    return token, jti, expires


def decode_access_token(token: str, settings: Settings) -> dict:
    """Raises jwt.PyJWTError for invalid/expired tokens."""
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM], options={"require": ["exp", "sub", "jti"]})
