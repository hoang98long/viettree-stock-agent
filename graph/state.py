"""Typed LangGraph state definitions."""

from __future__ import annotations

from typing import Any, TypedDict


JSONDict = dict[str, Any]
AlertList = list[JSONDict]


class StockAnalysisState(TypedDict, total=False):
    """Canonical shared state for the stock analysis graph."""

    symbol: str
    price_data: JSONDict
    indicators: JSONDict
    fundamentals: JSONDict
    sentiment: JSONDict
    prediction: JSONDict
    decision: JSONDict
    alerts: AlertList
    metadata: JSONDict
