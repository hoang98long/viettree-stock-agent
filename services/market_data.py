"""Market data provider service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging

import pandas as pd
import yfinance as yf

from services.cache import RedisCache
from services.config import Settings
from services.exceptions import MarketDataUnavailableError
from services.retry import retry_sync

LOGGER = logging.getLogger(__name__)


class MarketDataService:
    """Fetches and normalizes market OHLCV data."""

    def __init__(self, *, settings: Settings, cache: RedisCache) -> None:
        self.settings = settings
        self.cache = cache

    @retry_sync(attempts=3, delay_seconds=0.5, retry_on=(Exception,))
    def fetch_price_history(self, *, symbol: str, lookback_days: int) -> pd.DataFrame:
        cache_key = f"price-history:{symbol}:{lookback_days}"
        cached = self.cache.get_json(cache_key)
        if cached:
            LOGGER.info("market data cache hit symbol=%s lookback_days=%s", symbol, lookback_days)
            return pd.DataFrame(cached)

        end = datetime.now(tz=UTC)
        start = end - timedelta(days=lookback_days)
        LOGGER.info("fetching market data symbol=%s start=%s end=%s", symbol, start.date(), end.date())
        history = yf.Ticker(symbol).history(start=start, end=end, auto_adjust=False)
        if history.empty:
            raise MarketDataUnavailableError(f"no market data returned for {symbol}")

        frame = history.reset_index().rename(
            columns={
                "Date": "timestamp",
                "Datetime": "timestamp",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            }
        )
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
        normalized = frame[["timestamp", "open", "high", "low", "close", "volume"]]
        serialized = self.serialize_price_frame(normalized)
        self.cache.set_json(
            cache_key,
            serialized,
            self.settings.market_data_cache_ttl_seconds,
        )
        LOGGER.info("market data fetched symbol=%s rows=%s", symbol, len(normalized))
        return normalized

    @staticmethod
    def serialize_price_frame(frame: pd.DataFrame) -> dict[str, list]:
        result = frame.copy()
        result["timestamp"] = pd.to_datetime(result["timestamp"], utc=True).dt.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        return {
            "timestamp": result["timestamp"].tolist(),
            "open": result["open"].astype(float).tolist(),
            "high": result["high"].astype(float).tolist(),
            "low": result["low"].astype(float).tolist(),
            "close": result["close"].astype(float).tolist(),
            "volume": result["volume"].fillna(0).astype(float).tolist(),
        }
