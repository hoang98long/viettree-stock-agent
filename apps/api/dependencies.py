"""Dependency wiring for API handlers."""

from functools import lru_cache

from services.analysis_service import AnalysisService
from services.cache import RedisCache
from services.config import Settings, get_settings
from services.database import Database
from services.llm import OllamaClientFactory
from services.market_data import MarketDataService
from services.prediction_model import PredictionModelService
from services.sentiment_service import SentimentAnalysisService
from services.storage import AnalysisStorageService


@lru_cache
def get_analysis_service() -> AnalysisService:
    settings = get_settings()
    database = Database(settings)
    cache = RedisCache(settings)
    llm_factory = OllamaClientFactory(settings)

    return AnalysisService(
        settings=settings,
        market_data_service=MarketDataService(settings=settings, cache=cache),
        sentiment_service=SentimentAnalysisService(
            settings=settings,
            llm_factory=llm_factory,
        ),
        prediction_service=PredictionModelService(settings=settings),
        storage_service=AnalysisStorageService(
            settings=settings,
            database=database,
            cache=cache,
        ),
    )


def get_settings_dependency() -> Settings:
    return get_settings()
