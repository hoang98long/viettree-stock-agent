"""Redis-backed worker starter."""

from __future__ import annotations

import asyncio
import json
import logging

from schemas.analysis import WorkerAnalyzeRequest
from services.config import get_settings
from services.logging import configure_logging
from services.runtime import build_runtime

LOGGER = logging.getLogger(__name__)


async def run_worker() -> None:
    service = build_runtime()
    queue_name = get_settings().redis_analysis_queue
    LOGGER.info("worker started queue=%s", queue_name)

    while True:
        payload = service.storage_service.dequeue_analysis_request(queue_name)
        if payload is None:
            await asyncio.sleep(1.0)
            continue

        try:
            request = WorkerAnalyzeRequest.model_validate(json.loads(payload))
            await service.analyze_symbol(
                symbol=request.symbol,
                lookback_days=request.lookback_days,
                include_fundamentals=request.include_fundamentals,
                include_sentiment=request.include_sentiment,
                include_prediction=request.include_prediction,
            )
        except Exception:
            LOGGER.exception("worker request failed payload=%s", payload)


if __name__ == "__main__":
    configure_logging()
    asyncio.run(run_worker())
