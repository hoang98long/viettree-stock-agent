"""Redis-backed worker starter."""

import asyncio
import json
import logging

from services.analysis_service import AnalysisService
from services.cache import RedisCache
from services.config import get_settings
from services.database import Database
from services.llm import OllamaClientFactory
from services.market_data import MarketDataService
from services.prediction_model import PredictionModelService
from services.sentiment_service import SentimentAnalysisService
from services.storage import AnalysisStorageService

LOGGER = logging.getLogger(__name__)


def build_analysis_service() -> AnalysisService:
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


async def run_worker() -> None:
    service = build_analysis_service()
    queue_name = get_settings().redis_analysis_queue
    LOGGER.info("worker started queue=%s", queue_name)

    while True:
        payload = service.storage_service.dequeue_analysis_request(queue_name)
        if payload is None:
            await asyncio.sleep(1.0)
            continue

        request = json.loads(payload)
        await service.analyze_symbol(
            symbol=request["symbol"],
            lookback_days=request.get("lookback_days", 180),
            include_fundamentals=request.get("include_fundamentals", True),
            include_sentiment=request.get("include_sentiment", True),
            include_prediction=request.get("include_prediction", True),
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_worker())
