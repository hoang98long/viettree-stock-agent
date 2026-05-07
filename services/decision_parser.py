"""Deterministic decision scoring plus constrained LLM explanation."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import StockAnalysisState
from services.config import Settings


class DecisionEngine:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def decide(
        self,
        *,
        state: StockAnalysisState,
        llm: BaseChatModel,
    ) -> dict[str, Any]:
        score = 0.0
        indicators = state.get("indicators", {})
        fundamentals = state.get("fundamentals", {})
        sentiment = state.get("sentiment", {})
        prediction = state.get("prediction", {})

        rsi = indicators.get("rsi_14")
        macd_histogram = indicators.get("macd_histogram")
        trend = indicators.get("trend")
        if isinstance(rsi, (int, float)):
            if rsi < 35:
                score += 0.15
            elif rsi > 65:
                score -= 0.15
        if isinstance(macd_histogram, (int, float)):
            score += 0.2 if macd_histogram > 0 else -0.2
        if trend == "bullish":
            score += 0.2
        elif trend == "bearish":
            score -= 0.2

        if fundamentals.get("valuation") == "undervalued":
            score += 0.15
        elif fundamentals.get("valuation") == "overvalued":
            score -= 0.15

        sentiment_score = sentiment.get("score")
        if isinstance(sentiment_score, (int, float)):
            score += max(min(sentiment_score, 1.0), -1.0) * 0.15

        if prediction.get("direction") == "UP":
            score += float(prediction.get("confidence", 0.0)) * 0.15
        elif prediction.get("direction") == "DOWN":
            score -= float(prediction.get("confidence", 0.0)) * 0.15

        action = "HOLD"
        if score >= 0.25:
            action = "BUY"
        elif score <= -0.25:
            action = "SELL"

        confidence = min(abs(score), 1.0)
        explanation = self._generate_reasoning(
            llm=llm,
            state=state,
            action=action,
            confidence=confidence,
            score=score,
        )

        return {
            "action": action,
            "confidence": round(confidence, 4),
            "score": round(score, 4),
            "reasoning": explanation["reasoning"],
            "signal_breakdown": explanation["signal_breakdown"],
            "risk_flags": explanation["risk_flags"],
        }

    def _generate_reasoning(
        self,
        *,
        llm: BaseChatModel,
        state: StockAnalysisState,
        action: str,
        confidence: float,
        score: float,
    ) -> dict[str, Any]:
        system_prompt = (
            "You explain stock signals. Return strict JSON with keys "
            "reasoning, signal_breakdown, risk_flags. No markdown."
        )
        human_prompt = json.dumps(
            {
                "symbol": state["symbol"],
                "action": action,
                "confidence": round(confidence, 4),
                "score": round(score, 4),
                "indicators": state.get("indicators", {}),
                "fundamentals": state.get("fundamentals", {}),
                "sentiment": state.get("sentiment", {}),
                "prediction": state.get("prediction", {}),
            }
        )
        response = llm.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt),
            ]
        )
        content = response.content if isinstance(response.content, str) else ""
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            parsed = {}

        reasoning = parsed.get("reasoning")
        signal_breakdown = parsed.get("signal_breakdown")
        risk_flags = parsed.get("risk_flags")
        return {
            "reasoning": reasoning
            if isinstance(reasoning, str)
            else "Signals combined deterministically; LLM explanation fallback used.",
            "signal_breakdown": signal_breakdown
            if isinstance(signal_breakdown, list)
            else [],
            "risk_flags": risk_flags if isinstance(risk_flags, list) else [],
        }
