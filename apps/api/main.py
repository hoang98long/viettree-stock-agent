"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from apps.api.routes.analysis import router as analysis_router
from services.config import get_settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    settings.ensure_runtime_dirs()
    yield


app = FastAPI(
    title="Stock Agent AI",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(analysis_router, prefix="/v1")


@app.get("/healthz", tags=["system"])
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
