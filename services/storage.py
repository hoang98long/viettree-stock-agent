"""Persistence and queue-facing storage service."""

from __future__ import annotations

import json
import logging

from db.repositories import AnalysisRunRepository
from schemas.analysis import AnalysisResult, WorkerAnalyzeRequest
from services.cache import RedisCache
from services.config import Settings
from services.database import Database

LOGGER = logging.getLogger(__name__)


class AnalysisStorageService:
    def __init__(
        self,
        *,
        settings: Settings,
        database: Database,
        cache: RedisCache,
    ) -> None:
        self.settings = settings
        self.database = database
        self.cache = cache
        self._schema_initialized = False

    def persist_analysis(self, result: dict) -> None:
        parsed = AnalysisResult.model_validate(result)
        try:
            if not self._schema_initialized:
                self.database.create_schema()
                self._schema_initialized = True
            with self.database.session() as session:
                repo = AnalysisRunRepository(session)
                repo.create(
                    symbol=parsed.symbol,
                    decision=parsed.decision,
                    alerts=parsed.alerts,
                    metadata=parsed.metadata,
                )
        except Exception:
            LOGGER.exception("analysis persistence failed symbol=%s", parsed.symbol)

    def enqueue_analysis_request(self, payload: dict) -> None:
        request = WorkerAnalyzeRequest.model_validate(payload)
        self.cache.enqueue(
            self.settings.redis_analysis_queue,
            request.model_dump_json(),
        )

    def dequeue_analysis_request(self, queue_name: str) -> str | None:
        return self.cache.dequeue(queue_name)
