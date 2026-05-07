"""Technical indicator computation."""

from __future__ import annotations

import pandas as pd
import pandas_ta as ta


class TechnicalIndicatorService:
    """Computes indicators without LLM involvement."""

    def compute_from_serialized_prices(self, price_data: dict) -> dict:
        frame = pd.DataFrame(price_data)
        if frame.empty:
            raise ValueError("price_data is empty")

        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
        frame = frame.sort_values("timestamp").reset_index(drop=True)

        close = frame["close"]
        frame["sma_20"] = ta.sma(close, length=20)
        frame["sma_50"] = ta.sma(close, length=50)
        frame["ema_20"] = ta.ema(close, length=20)
        frame["rsi_14"] = ta.rsi(close, length=14)
        macd = ta.macd(close, fast=12, slow=26, signal=9)
        bbands = ta.bbands(close, length=20, std=2)

        latest = frame.iloc[-1]
        latest_macd = macd.iloc[-1] if macd is not None else pd.Series(dtype=float)
        latest_bbands = (
            bbands.iloc[-1] if bbands is not None else pd.Series(dtype=float)
        )

        trend = "neutral"
        if latest["sma_20"] > latest["sma_50"]:
            trend = "bullish"
        elif latest["sma_20"] < latest["sma_50"]:
            trend = "bearish"

        return {
            "sma_20": _to_float(latest.get("sma_20")),
            "sma_50": _to_float(latest.get("sma_50")),
            "ema_20": _to_float(latest.get("ema_20")),
            "rsi_14": _to_float(latest.get("rsi_14")),
            "macd": _to_float(latest_macd.get("MACD_12_26_9")),
            "macd_signal": _to_float(latest_macd.get("MACDs_12_26_9")),
            "macd_histogram": _to_float(latest_macd.get("MACDh_12_26_9")),
            "bb_upper": _to_float(latest_bbands.get("BBU_20_2.0")),
            "bb_middle": _to_float(latest_bbands.get("BBM_20_2.0")),
            "bb_lower": _to_float(latest_bbands.get("BBL_20_2.0")),
            "trend": trend,
        }


def _to_float(value) -> float | None:
    if pd.isna(value):
        return None
    return float(value)
