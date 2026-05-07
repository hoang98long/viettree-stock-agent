"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from apps.api.routes.analysis import router as analysis_router
from apps.api.schemas import ErrorResponse, HealthResponse
from services.config import get_settings
from services.logging import configure_logging

LOGGER = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    configure_logging()
    settings.ensure_runtime_dirs()
    LOGGER.info("api starting env=%s app=%s", settings.app_env, settings.app_name)
    yield
    LOGGER.info("api stopping app=%s", settings.app_name)


app = FastAPI(
    title="Stock Agent AI",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(analysis_router, prefix="/v1")


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    LOGGER.exception("unhandled application exception")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(detail="internal server error").model_dump(),
    )


@app.get("/healthz", tags=["system"], response_model=HealthResponse)
async def healthcheck() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.app_env,
    )
