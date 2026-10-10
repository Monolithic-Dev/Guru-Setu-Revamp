"""GuruSetu API entry point (CMP-02). Written once in final form (phase-0 T0.P2.1): later phases add router files
under `app/api/v1/` and fill the `ml` and `jobs` startup hooks, but never edit this file.
"""
import importlib
import logging
import pkgutil
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import database
from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.middleware import RequestContextMiddleware, configure_logging

API_PREFIX = "/api/v1"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schema" / "schema.cypher"

log = logging.getLogger("gurusetu.startup")


def _call_ml_startup() -> None:
    """P1 owns `app.ml.startup()` (loads the embedding model). Tolerate it missing; never swallow its errors."""
    from app import ml

    startup = getattr(ml, "startup", None)
    if startup is not None:
        startup()


def _include_routers(app: FastAPI) -> list[str]:
    """Auto-discovery: every module in app/api/v1 that exposes `router` is mounted under /api/v1."""
    from app.api import v1

    mounted: list[str] = []
    for module_info in sorted(pkgutil.iter_modules(v1.__path__), key=lambda m: m.name):
        module = importlib.import_module(f"{v1.__name__}.{module_info.name}")
        router = getattr(module, "router", None)
        if isinstance(router, APIRouter):
            app.include_router(router, prefix=API_PREFIX)
            mounted.append(module_info.name)
    return mounted


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    if settings.today_override is not None:
        log.warning({"event": "today_override_set", "value": settings.today_override.isoformat()})
    database.init_driver()
    database.wait_for_db()
    count = database.apply_schema(SCHEMA_PATH)
    log.info({"event": "schema_applied", "statements": count})
    _call_ml_startup()
    from app.services import jobs

    jobs.startup()
    try:
        yield
    finally:
        database.close_driver()


def create_app() -> FastAPI:
    settings = get_settings()  # raises ConfigError on a weak secret (SEC-10)
    configure_logging(settings.log_level)
    app = FastAPI(
        title="GuruSetu API",
        version="1.0.0",
        lifespan=lifespan,
        # The contract is docs/04-backend/openapi.yaml. No interactive docs: SEC-03 allows only login and health
        # without a token.
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    # Added first = inner. RequestContextMiddleware is added last so it is outermost and tags every response.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "PUT"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Request-ID"],
        expose_headers=["X-Request-ID", "Content-Disposition", "Retry-After"],
    )
    app.add_middleware(RequestContextMiddleware)
    register_error_handlers(app)
    _include_routers(app)
    return app


app = create_app()
