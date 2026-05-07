"""Redis cache and queue helpers."""

from __future__ import annotations

import json
import logging
from typing import Any

import redis

from services.config import Settings

LOGGER = logging.getLogger(__name__)


class RedisCache:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client: redis.Redis | None = None

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.Redis.from_url(
                self.settings.redis_url,
                decode_responses=True,
            )
        return self._client

    def get_json(self, key: str) -> dict[str, Any] | None:
        try:
            payload = self.client.get(key)
        except redis.RedisError:
            LOGGER.exception("redis get failed key=%s", key)
            return None
        try:
            return json.loads(payload) if payload else None
        except json.JSONDecodeError:
            LOGGER.exception("redis payload decode failed key=%s", key)
            return None

    def set_json(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        try:
            self.client.setex(key, ttl_seconds, json.dumps(value))
        except redis.RedisError:
            LOGGER.exception("redis set failed key=%s", key)

    def enqueue(self, queue_name: str, payload: str) -> None:
        try:
            self.client.lpush(queue_name, payload)
        except redis.RedisError:
            LOGGER.exception("redis enqueue failed queue=%s", queue_name)

    def dequeue(self, queue_name: str) -> str | None:
        try:
            item = self.client.brpop(queue_name, timeout=1)
        except redis.RedisError:
            LOGGER.exception("redis dequeue failed queue=%s", queue_name)
            return None
        return item[1] if item else None
