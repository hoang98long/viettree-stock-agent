"""Sentiment analysis service."""

from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage

from services.config import Settings
from services.llm import OllamaClientFactory


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

    def analyze_symbol(self, symbol: str) -> dict:
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

        return {
            "sentiment": parsed.get("sentiment", "neutral"),
            "score": score,
            "summary": parsed.get(
                "summary",
                "Sentiment response validation failed; neutral fallback used.",
            ),
            "status": "ok" if parsed else "fallback",
        }
