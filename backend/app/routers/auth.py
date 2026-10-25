"""Auth endpoints. Session = signed JWT in an HttpOnly cookie (revocable on logout)."""
import jwt
from fastapi import APIRouter, Depends, Request, Response

from app.core.config import Settings, get_settings
from app.core.security import create_access_token, decode_access_token
from app.db.mongo import get_db
from app.deps import get_current_user
from app.schemas.auth import AuthResponse, LoginRequest, MessageResponse, RegisterRequest, UserOut
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_session_cookie(response: Response, user: dict, settings: Settings) -> int:
    token, _, _ = create_access_token(str(user["_id"]), settings)
    max_age = settings.access_token_expire_minutes * 60
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        max_age=max_age,
        httponly=True,                       # JS can never read the token (XSS-safe)
        secure=settings.cookie_secure_effective,
        samesite=settings.cookie_samesite,   # CSRF mitigation (+ Origin check in main.py)
        path="/",
    )
    return max_age


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(payload: RegisterRequest, response: Response, db=Depends(get_db), settings: Settings = Depends(get_settings)):
    user = await auth_service.register_user(db, settings, payload.name, payload.email, payload.password)
    expires_in = _set_session_cookie(response, user, settings)  # sign the new user in
    return AuthResponse(user=UserOut.from_doc(user), expires_in=expires_in)


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, response: Response, db=Depends(get_db), settings: Settings = Depends(get_settings)):
    user = await auth_service.authenticate(db, settings, payload.email, payload.password)
    expires_in = _set_session_cookie(response, user, settings)
    return AuthResponse(user=UserOut.from_doc(user), expires_in=expires_in)


@router.post("/logout", response_model=MessageResponse)
async def logout(request: Request, response: Response, db=Depends(get_db), settings: Settings = Depends(get_settings)):
    """Always clears the cookie; also revokes the token server-side if it is still valid."""
    token = request.cookies.get(settings.cookie_name)
    if token:
        try:
            payload = decode_access_token(token, settings)
            from datetime import datetime, timezone

            await auth_service.revoke_token(db, payload["jti"], datetime.fromtimestamp(payload["exp"], tz=timezone.utc))
        except jwt.PyJWTError:
            pass
    response.delete_cookie(settings.cookie_name, path="/", httponly=True, secure=settings.cookie_secure_effective, samesite=settings.cookie_samesite)
    return MessageResponse(message="Logged out")


@router.get("/me", response_model=UserOut)
async def me(user: dict = Depends(get_current_user)):
    return UserOut.from_doc(user)
