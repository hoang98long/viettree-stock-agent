"""Top-level analysis orchestration service."""

from __future__ import annotations

import logging

from agents.alert_agent import AlertAgent
from agents.data_agent import DataAgent
from agents.decision_agent import DecisionAgent
from agents.fundamental_agent import FundamentalAgent
from agents.prediction_agent import PredictionAgent
from agents.sentiment_agent import SentimentAgent
from agents.technical_agent import TechnicalAgent
from graph.graph_builder import build_analysis_graph
from graph.state import StockAnalysisState
from schemas.analysis import AnalysisOptions, AnalysisResult
from services.config import Settings
from services.exceptions import ValidationError
from services.fundamental_service import FundamentalAnalysisService
from services.indicator_service import TechnicalIndicatorService
from services.llm import OllamaClientFactory
from services.market_data import MarketDataService
from services.prediction_model import PredictionModelService
from services.sentiment_service import SentimentAnalysisService
from services.storage import AnalysisStorageService

LOGGER = logging.getLogger(__name__)


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
            decision_agent=DecisionAgent(llm_factory=llm_factory),
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
            raise ValidationError("symbol must not be empty")

        options = AnalysisOptions(
            lookback_days=lookback_days,
            include_fundamentals=include_fundamentals,
            include_sentiment=include_sentiment,
            include_prediction=include_prediction,
        )
        LOGGER.info("analysis started symbol=%s", normalized_symbol)

        initial_state = self._build_initial_state(normalized_symbol, options)
        result = self.graph.invoke(initial_state)
        parsed = AnalysisResult.model_validate(result)
        self.storage_service.persist_analysis(parsed.model_dump())
        LOGGER.info(
            "analysis finished symbol=%s action=%s confidence=%s",
            parsed.symbol,
            parsed.decision.get("action"),
            parsed.decision.get("confidence"),
        )
        return parsed.model_dump()

    def _build_initial_state(
        self,
        symbol: str,
        options: AnalysisOptions,
    ) -> StockAnalysisState:
        return {
            "symbol": symbol,
            "price_data": {},
            "indicators": {},
            "fundamentals": {},
            "sentiment": {},
            "prediction": {},
            "decision": {},
            "alerts": [],
            "metadata": {
                "lookback_days": options.lookback_days,
                "include_fundamentals": options.include_fundamentals,
                "include_sentiment": options.include_sentiment,
                "include_prediction": options.include_prediction,
                "architecture": "agentic+ml+rag-ready",
                "async_ingestion_ready": True,
                "websocket_streaming_ready": True,
                "backtesting_ready": True,
            },
        }
