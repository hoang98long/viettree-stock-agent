"""Sentiment analysis service."""

from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from services.config import Settings
from services.llm import OllamaClientFactory
from services.retry import retry_sync

LOGGER = logging.getLogger(__name__)


class SentimentAnalysisService:
    """Short-prompt LLM sentiment estimator."""

    def __init__(
        self,
        *,
        settings: Settings,
        llm_factory: OllamaClientFactory,
    ) -> None:
        self.settings = settings
        self.llm_factory = llm_factory

    @retry_sync(attempts=2, delay_seconds=0.25, retry_on=(Exception,))
    def analyze_symbol(self, symbol: str) -> dict:
        LOGGER.info("running sentiment analysis symbol=%s", symbol)
        llm = self.llm_factory.build_reasoning_llm()
        response = llm.invoke(
            [
                SystemMessage(
                    content=(
                        "Return strict JSON with keys sentiment, score, summary. "
                        "Score must be between -1 and 1."
                    )
                ),
                HumanMessage(
                    content=(
                        f"Estimate current market sentiment for stock ticker {symbol}. "
                        "Keep it concise."
                    )
                ),
            ]
        )
        content = response.content if isinstance(response.content, str) else ""
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            parsed = {}

        score = parsed.get("score", 0.0)
        if not isinstance(score, (int, float)):
            score = 0.0
        score = max(min(float(score), 1.0), -1.0)

        result = {
            "sentiment": parsed.get("sentiment", "neutral"),
            "score": score,
            "summary": parsed.get(
                "summary",
                "Sentiment response validation failed; neutral fallback used.",
            ),
            "status": "ok" if parsed else "fallback",
        }
        LOGGER.info("sentiment analysis completed symbol=%s status=%s", symbol, result["status"])
        return result
