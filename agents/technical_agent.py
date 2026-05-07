"""Technical analysis agent."""

from services.indicator_service import TechnicalIndicatorService

from graph.state import StockAnalysisState


class TechnicalAgent:
    """Computes indicators from normalized price history."""

    def __init__(self, indicator_service: TechnicalIndicatorService) -> None:
        self.indicator_service = indicator_service

    def __call__(self, state: StockAnalysisState) -> StockAnalysisState:
        indicators = self.indicator_service.compute_from_serialized_prices(
            state["price_data"]
        )
        return {"indicators": indicators}
