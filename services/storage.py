"""Persistence and queue-facing storage service."""

from __future__ import annotations

import json
import logging

from db.repositories import AnalysisRunRepository
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

    def persist_analysis(self, result: dict) -> None:
        try:
            self.database.create_schema()
            with self.database.session() as session:
                repo = AnalysisRunRepository(session)
                repo.create(
                    symbol=result["symbol"],
                    decision=result["decision"],
                    alerts=result["alerts"],
                    metadata=result["metadata"],
                )
        except Exception:
            LOGGER.exception("analysis persistence failed symbol=%s", result.get("symbol"))

    def enqueue_analysis_request(self, payload: dict) -> None:
        self.cache.enqueue(self.settings.redis_analysis_queue, json.dumps(payload))

    def dequeue_analysis_request(self, queue_name: str) -> str | None:
        return self.cache.dequeue(queue_name)
