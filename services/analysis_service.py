"""Top-level analysis orchestration service."""

from __future__ import annotations

from agents.alert_agent import AlertAgent
from agents.data_agent import DataAgent
from agents.decision_agent import DecisionAgent
from agents.fundamental_agent import FundamentalAgent
from agents.prediction_agent import PredictionAgent
from agents.sentiment_agent import SentimentAgent
from agents.technical_agent import TechnicalAgent
from graph.builder import build_analysis_graph
from graph.state import StockAnalysisState
from services.config import Settings
from services.decision_parser import DecisionEngine
from services.fundamental_service import FundamentalAnalysisService
from services.indicator_service import TechnicalIndicatorService
from services.llm import OllamaClientFactory
from services.market_data import MarketDataService
from services.prediction_model import PredictionModelService
from services.sentiment_service import SentimentAnalysisService
from services.storage import AnalysisStorageService


class AnalysisService:
    """Composes agents and exposes one symbol-level analysis call."""

    def __init__(
        self,
        *,
        settings: Settings,
        market_data_service: MarketDataService,
        sentiment_service: SentimentAnalysisService,
        prediction_service: PredictionModelService,
        storage_service: AnalysisStorageService,
    ) -> None:
        self.settings = settings
        self.market_data_service = market_data_service
        self.sentiment_service = sentiment_service
        self.prediction_service = prediction_service
        self.storage_service = storage_service

        llm_factory = OllamaClientFactory(settings)
        self.graph = build_analysis_graph(
            data_agent=DataAgent(market_data_service),
            technical_agent=TechnicalAgent(TechnicalIndicatorService()),
            fundamental_agent=FundamentalAgent(FundamentalAnalysisService()),
            sentiment_agent=SentimentAgent(sentiment_service),
            prediction_agent=PredictionAgent(prediction_service),
            decision_agent=DecisionAgent(
                llm_factory=llm_factory,
                decision_engine=DecisionEngine(settings=settings),
            ),
            alert_agent=AlertAgent(),
        )

    async def analyze_symbol(
        self,
        *,
        symbol: str,
        lookback_days: int,
        include_fundamentals: bool,
        include_sentiment: bool,
        include_prediction: bool,
    ) -> dict:
        normalized_symbol = symbol.strip().upper()
        if not normalized_symbol:
            raise ValueError("symbol must not be empty")

        initial_state: StockAnalysisState = {
            "symbol": normalized_symbol,
            "price_data": {},
            "indicators": {},
            "fundamentals": {},
            "sentiment": {},
            "prediction": {},
            "decision": {},
            "alerts": [],
            "metadata": {
                "lookback_days": lookback_days,
                "include_fundamentals": include_fundamentals,
                "include_sentiment": include_sentiment,
                "include_prediction": include_prediction,
                "architecture": "agentic+ml+rag-ready",
            },
        }

        result = self.graph.invoke(initial_state)
        self.storage_service.persist_analysis(result)
        return result
