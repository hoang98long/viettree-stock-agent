"""Market data agent."""

from services.market_data import MarketDataService

from graph.state import StockAnalysisState


class DataAgent:
    """Fetches and normalizes raw market data."""

    def __init__(self, market_data_service: MarketDataService) -> None:
        self.market_data_service = market_data_service

    def __call__(self, state: StockAnalysisState) -> StockAnalysisState:
        symbol = state["symbol"]
        lookback_days = int(state["metadata"].get("lookback_days", 180))
        price_frame = self.market_data_service.fetch_price_history(
            symbol=symbol,
            lookback_days=lookback_days,
        )
        normalized = self.market_data_service.serialize_price_frame(price_frame)

        metadata = dict(state.get("metadata", {}))
        metadata["price_points"] = len(price_frame)
        metadata["latest_close"] = float(price_frame["close"].iloc[-1])

        return {
            "price_data": normalized,
            "metadata": metadata,
        }
