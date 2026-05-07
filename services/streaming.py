"""WebSocket streaming scaffolding."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any


class StreamBroker:
    """In-memory broker placeholder for future streaming updates."""

    def __init__(self) -> None:
        self._queues: dict[str, list[asyncio.Queue[dict[str, Any]]]] = defaultdict(list)

    async def subscribe(self, channel: str) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._queues[channel].append(queue)
        return queue

    async def publish(self, channel: str, payload: dict[str, Any]) -> None:
        for queue in self._queues.get(channel, []):
            await queue.put(payload)

    async def unsubscribe(self, channel: str, queue: asyncio.Queue[dict[str, Any]]) -> None:
        if channel in self._queues and queue in self._queues[channel]:
            self._queues[channel].remove(queue)
