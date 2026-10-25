"""Uniform, non-sensitive error responses (no stack traces, no echoed passwords)."""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pymongo.errors import PyMongoError

logger = logging.getLogger("app.errors")


class AppError(Exception):
    """Expected, client-safe error. `extra` is merged into the JSON body."""

    def __init__(self, status_code: int, code: str, message: str, extra: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.extra = extra or {}


def not_found(what: str = "Resource") -> AppError:
    return AppError(404, "not_found", f"{what} not found")


def _body(code: str, message: str, **extra) -> dict:
    return {"detail": message, "code": code, **extra}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content=_body(exc.code, exc.message, **exc.extra))

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_: Request, exc: RequestValidationError):
        # Build our own list: FastAPI's default includes the raw `input` (could be a password).
        errors = []
        for err in exc.errors():
            loc = [str(p) for p in err.get("loc", ()) if p not in ("body", "query", "path")]
            msg = str(err.get("msg", "Invalid value"))
            if msg.startswith("Value error, "):
                msg = msg[len("Value error, "):]
            errors.append({"field": ".".join(loc) or "body", "message": msg})
        first = errors[0]["message"] if errors else "Invalid request"
        return JSONResponse(status_code=422, content=_body("validation_error", first, errors=errors))

    @app.exception_handler(PyMongoError)
    async def mongo_handler(request: Request, exc: PyMongoError):
        logger.error("MongoDB error on %s %s: %s", request.method, request.url.path, type(exc).__name__)
        return JSONResponse(status_code=503, content=_body("database_unavailable", "The database is temporarily unavailable. Please try again."))

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception):
        logger.error("Unhandled error on %s %s: %s", request.method, request.url.path, type(exc).__name__)
        return JSONResponse(status_code=500, content=_body("internal_error", "Something went wrong on our side. Please try again."))
