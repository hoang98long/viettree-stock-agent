"""Shared agent helpers."""

from __future__ import annotations

from typing import Protocol

from graph.state import StockAnalysisState


class GraphAgent(Protocol):
    def __call__(self, state: StockAnalysisState) -> StockAnalysisState:
        """Execute a unit of graph work and return a partial state."""
