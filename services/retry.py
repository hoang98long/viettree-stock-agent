"""Small retry helpers for transient dependency failures."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

LOGGER = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


def retry_sync(
    *,
    attempts: int = 3,
    delay_seconds: float = 0.5,
    backoff_multiplier: float = 2.0,
    retry_on: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            last_error: Exception | None = None
            delay = delay_seconds
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except retry_on as exc:
                    last_error = exc
                    if attempt >= attempts:
                        break
                    LOGGER.warning(
                        "retrying function=%s attempt=%s/%s error=%s",
                        func.__name__,
                        attempt,
                        attempts,
                        exc,
                    )
                    time.sleep(delay)
                    delay *= backoff_multiplier
            assert last_error is not None
            raise last_error

        return wrapper

    return decorator
