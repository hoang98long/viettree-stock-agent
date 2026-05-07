"""Fundamental analysis agent."""

from services.fundamental_service import FundamentalAnalysisService

from graph.state import StockAnalysisState


class FundamentalAgent:
    """Computes deterministic fundamental signals from issuer data."""

    def __init__(self, fundamental_service: FundamentalAnalysisService) -> None:
        self.fundamental_service = fundamental_service

    def __call__(self, state: StockAnalysisState) -> StockAnalysisState:
        if not state["metadata"].get("include_fundamentals", True):
            return {"fundamentals": {"status": "skipped"}}

        fundamentals = self.fundamental_service.build_snapshot(state["symbol"])
        return {"fundamentals": fundamentals}
