"""Shared pytest fixtures and deterministic test doubles."""

from __future__ import annotations

from typing import Any

import pandas as pd
import pytest

from agents.alert_agent import AlertAgent
from agents.data_agent import DataAgent
from agents.decision_agent import DecisionAgent
from agents.fundamental_agent import FundamentalAgent
from agents.prediction_agent import PredictionAgent
from agents.sentiment_agent import SentimentAgent
from agents.technical_agent import TechnicalAgent
from configs.settings import Settings
from graph.graph_builder import build_analysis_graph
from services.fundamental_service import FundamentalAnalysisService
from services.indicator_service import TechnicalIndicatorService
from services.prediction_model import PredictionModelService


class FakeResponse:
    def __init__(self, content: str) -> None:
        self.content = content


class FakeLLM:
    def __init__(self, content: str) -> None:
        self.content = content
        self.calls: list[list[Any]] = []

    def invoke(self, messages: list[Any]) -> FakeResponse:
        self.calls.append(messages)
        return FakeResponse(self.content)


class FakeLLMFactory:
    def __init__(self, llm: FakeLLM) -> None:
        self.llm = llm

    def build_reasoning_llm(self) -> FakeLLM:
        return self.llm


class FakeMarketDataService:
    def __init__(self, frame: pd.DataFrame) -> None:
        self.frame = frame

    def fetch_price_history(self, *, symbol: str, lookback_days: int) -> pd.DataFrame:
        return self.frame.copy()

    def serialize_price_frame(self, frame: pd.DataFrame) -> dict[str, list]:
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
            "volume": result["volume"].astype(float).tolist(),
        }


class FakeSentimentService:
    def analyze_symbol(self, symbol: str) -> dict[str, Any]:
        return {
            "sentiment": "positive",
            "score": 0.4,
            "summary": f"Positive sentiment for {symbol}.",
            "status": "ok",
        }


@pytest.fixture
def settings() -> Settings:
    return Settings(
        app_env="test",
        prediction_model_path="models/stock_trending_model.pt",
    )


@pytest.fixture
def sample_price_frame() -> pd.DataFrame:
    rows = []
    base_timestamp = pd.Timestamp("2025-01-01T00:00:00Z")
    price = 100.0
    for index in range(80):
        open_price = price + 0.2
        high_price = open_price + 1.0
        low_price = open_price - 1.2
        close_price = open_price + 0.4 + (index * 0.03)
        volume = 1_000_000 + (index * 1000)
        rows.append(
            {
                "timestamp": base_timestamp + pd.Timedelta(days=index),
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": volume,
            }
        )
        price = close_price
    return pd.DataFrame(rows)


@pytest.fixture
def serialized_price_data(sample_price_frame: pd.DataFrame) -> dict[str, list]:
    service = FakeMarketDataService(sample_price_frame)
    return service.serialize_price_frame(sample_price_frame)


@pytest.fixture
def llm_json_response() -> str:
    return (
        '{"reasoning":"Deterministic signals lean bullish with manageable risk.",'
        '"signal_breakdown":["RSI is supportive","MACD is positive","ML signal is secondary"],'
        '"risk_flags":["Sentiment can reverse quickly"]}'
    )


@pytest.fixture
def fake_llm(llm_json_response: str) -> FakeLLM:
    return FakeLLM(llm_json_response)


@pytest.fixture
def decision_agent(fake_llm: FakeLLM) -> DecisionAgent:
    return DecisionAgent(llm_factory=FakeLLMFactory(fake_llm))


@pytest.fixture
def prediction_service(settings: Settings) -> PredictionModelService:
    return PredictionModelService(settings=settings)


@pytest.fixture
def analysis_graph(
    sample_price_frame: pd.DataFrame,
    settings: Settings,
    fake_llm: FakeLLM,
) :
    market_data = FakeMarketDataService(sample_price_frame)
    graph = build_analysis_graph(
        data_agent=DataAgent(market_data),
        technical_agent=TechnicalAgent(TechnicalIndicatorService()),
        fundamental_agent=FundamentalAgent(FundamentalAnalysisService()),
        sentiment_agent=SentimentAgent(FakeSentimentService()),
        prediction_agent=PredictionAgent(PredictionModelService(settings=settings)),
        decision_agent=DecisionAgent(llm_factory=FakeLLMFactory(fake_llm)),
        alert_agent=AlertAgent(),
    )
    return graph
