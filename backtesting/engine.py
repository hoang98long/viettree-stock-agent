"""Backtesting engine scaffolding."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class BacktestRequest:
    symbol: str
    start_date: str
    end_date: str
    strategy_config: dict[str, Any]


class BacktestEngine:
    """Placeholder for replaying the graph against historical data."""

    def run(self, request: BacktestRequest) -> dict[str, Any]:
        # TODO: implement historical replay against deterministic market snapshots.
        return {
            "status": "not_implemented",
            "symbol": request.symbol,
            "start_date": request.start_date,
            "end_date": request.end_date,
        }
