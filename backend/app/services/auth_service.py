"""User registration, authentication and token revocation."""
from datetime import datetime

from pymongo.errors import DuplicateKeyError

from app.core.config import Settings
from app.core.errors import AppError
from app.core.security import hash_password, verify_password
from app.core.timeutil import utcnow

# Pre-computed hash so login takes similar time whether or not the email exists.
_DUMMY_HASH: str | None = None


def _dummy_hash(settings: Settings) -> str:
    global _DUMMY_HASH
    if _DUMMY_HASH is None:
        _DUMMY_HASH = hash_password("dummy-password-1", settings.bcrypt_rounds)
    return _DUMMY_HASH


async def register_user(db, settings: Settings, name: str, email: str, password: str) -> dict:
    if await db.users.find_one({"email": email}, {"_id": 1}):
        raise AppError(409, "email_taken", "An account with this email already exists.", {"errors": [{"field": "email", "message": "An account with this email already exists."}]})
    now = utcnow()
    doc = {
        "name": name,
        "email": email,
        "password_hash": hash_password(password, settings.bcrypt_rounds),
        "created_at": now,
        "updated_at": now,
    }
    try:
        res = await db.users.insert_one(doc)
    except DuplicateKeyError:  # race condition: unique index is the source of truth
        raise AppError(409, "email_taken", "An account with this email already exists.", {"errors": [{"field": "email", "message": "An account with this email already exists."}]})
    doc["_id"] = res.inserted_id
    return doc


async def authenticate(db, settings: Settings, email: str, password: str) -> dict:
    user = await db.users.find_one({"email": email})
    stored = user["password_hash"] if user else _dummy_hash(settings)
    ok = verify_password(password, stored)
    if not user or not ok:
        raise AppError(401, "invalid_credentials", "Invalid email or password.")
    return user


async def revoke_token(db, jti: str, expires_at: datetime) -> None:
    try:
        await db.revoked_tokens.insert_one({"_id": jti, "expires_at": expires_at})
    except DuplicateKeyError:
        pass


async def is_token_revoked(db, jti: str) -> bool:
    return await db.revoked_tokens.find_one({"_id": jti}, {"_id": 1}) is not None
