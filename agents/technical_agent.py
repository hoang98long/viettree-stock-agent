"""Technical analysis agent.

This agent is deterministic by design. It must never use an LLM for indicator
calculation or signal extraction.
"""

from __future__ import annotations

from graph.state import StockAnalysisState
from services.indicator_service import TechnicalIndicatorService


class TechnicalAgent:
    """Computes production-facing technical indicators from normalized prices."""

    def __init__(self, indicator_service: TechnicalIndicatorService) -> None:
        self.indicator_service = indicator_service

    def __call__(self, state: StockAnalysisState) -> StockAnalysisState:
        price_data = state.get("price_data") or {}
        if not price_data:
            raise ValueError("technical_agent requires non-empty price_data")

        raw_indicators = self.indicator_service.compute_from_serialized_prices(price_data)
        indicators = self._build_indicator_payload(raw_indicators)
        return {"indicators": indicators}

    def _build_indicator_payload(self, raw_indicators: dict) -> dict:
        # TODO: add ATR, ADX, stochastic oscillator, and volume indicators once signal contracts are defined.
        return {
            "rsi": {
                "period": 14,
                "value": raw_indicators.get("rsi_14"),
            },
            "macd": {
                "fast": 12,
                "slow": 26,
                "signal": 9,
                "line": raw_indicators.get("macd"),
                "signal_line": raw_indicators.get("macd_signal"),
                "histogram": raw_indicators.get("macd_histogram"),
            },
            "bollinger_bands": {
                "length": 20,
                "std_dev": 2,
                "upper": raw_indicators.get("bb_upper"),
                "middle": raw_indicators.get("bb_middle"),
                "lower": raw_indicators.get("bb_lower"),
            },
            "trend": {
                "sma_20": raw_indicators.get("sma_20"),
                "sma_50": raw_indicators.get("sma_50"),
                "ema_20": raw_indicators.get("ema_20"),
                "bias": raw_indicators.get("trend"),
            },
            "status": "ok",
        }
