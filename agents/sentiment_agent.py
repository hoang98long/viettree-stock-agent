"""Sentiment analysis agent."""

from services.sentiment_service import SentimentAnalysisService

from graph.state import StockAnalysisState


class SentimentAgent:
    """Uses the local LLM for short-form sentiment reasoning."""

    def __init__(self, sentiment_service: SentimentAnalysisService) -> None:
        self.sentiment_service = sentiment_service

    def __call__(self, state: StockAnalysisState) -> StockAnalysisState:
        if not state["metadata"].get("include_sentiment", True):
            return {"sentiment": {"status": "skipped"}}

        sentiment = self.sentiment_service.analyze_symbol(state["symbol"])
        return {"sentiment": sentiment}
