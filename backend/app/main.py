"""FastAPI application factory."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.db.mongo import close_client, get_db, init_indexes
from app.db.qdrant import close_qdrant, ensure_collection, get_qdrant
from app.routers import auth, chat, conversations

logger = logging.getLogger("app")
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    await init_indexes(get_db())  # fail fast if MongoDB is unreachable
    try:
        await ensure_collection(get_qdrant(), settings)
    except RuntimeError:
        raise  # embedding-dimension mismatch is a config bug: stop loudly
    except Exception as exc:
        logger.warning("Qdrant not ready (%s). Chat retrieval will return 503 until it is up.", type(exc).__name__)
    yield
    await close_qdrant()
    await close_client()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Hyper-Personalized Health & Fitness Coach API",
        version="1.0.0",
        lifespan=lifespan,
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

    @app.middleware("http")
    async def origin_check(request: Request, call_next):
        """CSRF defence-in-depth for cookie auth: reject state-changing requests from foreign origins."""
        if request.method in UNSAFE_METHODS:
            origin = request.headers.get("origin")
            if origin and origin.rstrip("/") not in settings.cors_origin_list:
                return JSONResponse(status_code=403, content={"detail": "Origin not allowed", "code": "origin_not_allowed"})
        return await call_next(request)

    register_exception_handlers(app)
    app.include_router(auth.router)
    app.include_router(conversations.router)
    app.include_router(chat.router)
    return app


app = create_app()
