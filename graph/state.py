"""Typed LangGraph state definitions."""

from typing import Any, TypedDict


class StockAnalysisState(TypedDict, total=False):
    symbol: str
    price_data: dict[str, Any]
    indicators: dict[str, Any]
    fundamentals: dict[str, Any]
    sentiment: dict[str, Any]
    prediction: dict[str, Any]
    decision: dict[str, Any]
    alerts: list[dict[str, Any]]
    metadata: dict[str, Any]
