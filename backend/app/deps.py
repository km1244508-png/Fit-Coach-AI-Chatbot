"""Shared FastAPI dependencies."""
from bson import ObjectId
from fastapi import Depends, Request

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.core.security import decode_access_token
from app.db.mongo import get_db
from app.services.auth_service import is_token_revoked


async def get_current_user(request: Request, db=Depends(get_db), settings: Settings = Depends(get_settings)) -> dict:
    token = request.cookies.get(settings.cookie_name)
    if not token:
        raise AppError(401, "not_authenticated", "Not authenticated. Please log in.")
    try:
        payload = decode_access_token(token, settings)
        user_id = ObjectId(payload["sub"])
    except Exception:  # bad signature, expired, malformed sub, ...
        raise AppError(401, "invalid_token", "Your session is invalid or expired. Please log in again.")
    if await is_token_revoked(db, payload["jti"]):
        raise AppError(401, "invalid_token", "Your session has ended. Please log in again.")
    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise AppError(401, "invalid_token", "Your session is invalid or expired. Please log in again.")
    return user
