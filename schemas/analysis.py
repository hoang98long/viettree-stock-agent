"""Shared domain schemas for analysis workflows."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AnalysisOptions(BaseModel):
    lookback_days: int = Field(default=180, ge=60, le=1000)
    include_fundamentals: bool = True
    include_sentiment: bool = True
    include_prediction: bool = True


class AnalysisResult(BaseModel):
    symbol: str
    decision: dict[str, Any]
    alerts: list[dict[str, Any]]
    indicators: dict[str, Any]
    fundamentals: dict[str, Any]
    sentiment: dict[str, Any]
    prediction: dict[str, Any]
    metadata: dict[str, Any]


class WorkerAnalyzeRequest(AnalysisOptions):
    symbol: str = Field(..., min_length=1, max_length=12)
