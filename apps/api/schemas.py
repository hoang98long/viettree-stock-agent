"""Request and response schemas for the HTTP API."""

from pydantic import BaseModel, Field
from schemas.analysis import AnalysisResult


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str


class ErrorResponse(BaseModel):
    detail: str


class AnalysisResponse(AnalysisResult):
    pass
