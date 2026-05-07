"""Async ingestion scaffolding for future background pipelines."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class IngestionJob:
    source_type: str
    symbol: str
    payload: dict[str, Any]


class AsyncIngestionCoordinator:
    """Placeholder boundary for async ingestion workers and queues."""

    async def submit(self, job: IngestionJob) -> None:
        # TODO: wire this to Redis streams, Kafka, or a task queue for async ingestion.
        _ = job

