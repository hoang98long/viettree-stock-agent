"""Request and response schemas for the HTTP API."""

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str


class ErrorResponse(BaseModel):
    detail: str


class AnalysisResponse(BaseModel):
    symbol: str
    decision: dict[str, Any]
    alerts: list[dict[str, Any]]
    indicators: dict[str, Any]
    fundamentals: dict[str, Any]
    sentiment: dict[str, Any]
    prediction: dict[str, Any]
    metadata: dict[str, Any]


class AnalyzeQueryParams(BaseModel):
    lookback_days: int = Field(default=180, ge=60, le=1000)
    include_fundamentals: bool = True
    include_sentiment: bool = True
    include_prediction: bool = True
