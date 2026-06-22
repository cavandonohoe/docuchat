"""FastAPI application factory."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import chat as chat_router
from app.api import documents as documents_router
from app.api import health as health_router
from app.core.config import get_settings
from app.core.exceptions import (
    DocumentNotFound,
    FileTooLarge,
    UnsupportedFileType,
)
from app.core.logging import configure_logging
from app.db.init_db import init_db
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    try:
        init_db()
    except Exception:  # pragma: no cover - startup failure is fatal
        logger.exception("Failed to initialize database")
        raise
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="docuchat",
        version=__version__,
        description="RAG over uploaded documents with cited answers.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router.router)
    app.include_router(documents_router.router)
    app.include_router(chat_router.router)

    @app.exception_handler(UnsupportedFileType)
    async def _unsupported(_, exc: UnsupportedFileType):
        return JSONResponse(status_code=415, content={"detail": str(exc)})

    @app.exception_handler(FileTooLarge)
    async def _too_large(_, exc: FileTooLarge):
        return JSONResponse(status_code=413, content={"detail": str(exc)})

    @app.exception_handler(DocumentNotFound)
    async def _not_found(_, exc: DocumentNotFound):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    return app


app = create_app()
