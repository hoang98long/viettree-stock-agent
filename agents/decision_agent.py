"""Decision synthesis agent.

This node uses a hybrid approach:
- deterministic scoring dominates action selection
- the LLM explains and lightly refines presentation
- the ML model is only one input signal and never overrides the full decision
"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import StockAnalysisState
from services.llm import OllamaClientFactory


class DecisionAgent:
    """Combines technical, sentiment, fundamentals, and ML signals."""

    def __init__(
        self,
        llm_factory: OllamaClientFactory,
        decision_engine: object | None = None,
    ) -> None:
        self.llm_factory = llm_factory
        self.decision_engine = decision_engine

    def __call__(self, state: StockAnalysisState) -> StockAnalysisState:
        deterministic = self._score_signals(state)
        llm = self.llm_factory.build_reasoning_llm()
        explanation = self._generate_llm_explanation(state=state, decision=deterministic, llm=llm)

        decision = {
            "action": deterministic["action"],
            "confidence": deterministic["confidence"],
            "risk_level": deterministic["risk_level"],
            "score": deterministic["score"],
            "reasoning": explanation["reasoning"],
            "signal_breakdown": explanation["signal_breakdown"],
            "risk_flags": explanation["risk_flags"],
            "deterministic_breakdown": deterministic["breakdown"],
            "llm_refined": True,
            "model_role": "explanation_only",
        }
        return {"decision": decision}

    def _score_signals(self, state: StockAnalysisState) -> dict[str, Any]:
        indicators = state.get("indicators", {})
        fundamentals = state.get("fundamentals", {})
        sentiment = state.get("sentiment", {})
        prediction = state.get("prediction", {})

        breakdown: list[dict[str, Any]] = []
        score = 0.0

        technical_score, technical_breakdown = self._score_technical(indicators)
        score += technical_score
        breakdown.extend(technical_breakdown)

        fundamental_score, fundamental_breakdown = self._score_fundamentals(fundamentals)
        score += fundamental_score
        breakdown.extend(fundamental_breakdown)

        sentiment_score, sentiment_breakdown = self._score_sentiment(sentiment)
        score += sentiment_score
        breakdown.extend(sentiment_breakdown)

        prediction_score, prediction_breakdown = self._score_prediction(prediction)
        score += prediction_score
        breakdown.extend(prediction_breakdown)

        action = "HOLD"
        if score >= 0.30:
            action = "BUY"
        elif score <= -0.30:
            action = "SELL"

        confidence = round(min(abs(score), 1.0), 4)
        risk_level = self._derive_risk_level(
            score=score,
            indicators=indicators,
            sentiment=sentiment,
            prediction=prediction,
        )

        return {
            "action": action,
            "confidence": confidence,
            "risk_level": risk_level,
            "score": round(score, 4),
            "breakdown": breakdown,
        }

    def _score_technical(self, indicators: dict[str, Any]) -> tuple[float, list[dict[str, Any]]]:
        score = 0.0
        breakdown: list[dict[str, Any]] = []

        rsi_value = (((indicators.get("rsi") or {}).get("value")))
        if isinstance(rsi_value, (int, float)):
            if rsi_value < 35:
                score += 0.15
                breakdown.append({"signal": "rsi", "effect": 0.15, "detail": "RSI indicates oversold conditions."})
            elif rsi_value > 65:
                score -= 0.15
                breakdown.append({"signal": "rsi", "effect": -0.15, "detail": "RSI indicates overbought conditions."})

        macd_histogram = ((indicators.get("macd") or {}).get("histogram"))
        if isinstance(macd_histogram, (int, float)):
            effect = 0.20 if macd_histogram > 0 else -0.20
            score += effect
            breakdown.append(
                {
                    "signal": "macd",
                    "effect": effect,
                    "detail": "MACD momentum is positive." if effect > 0 else "MACD momentum is negative.",
                }
            )

        trend_bias = ((indicators.get("trend") or {}).get("bias"))
        if trend_bias == "bullish":
            score += 0.20
            breakdown.append({"signal": "trend", "effect": 0.20, "detail": "Moving-average trend is bullish."})
        elif trend_bias == "bearish":
            score -= 0.20
            breakdown.append({"signal": "trend", "effect": -0.20, "detail": "Moving-average trend is bearish."})

        bbands = indicators.get("bollinger_bands") or {}
        upper = bbands.get("upper")
        lower = bbands.get("lower")
        middle = bbands.get("middle")
        if all(isinstance(value, (int, float)) for value in (upper, lower, middle)):
            band_width = upper - lower
            if band_width > 0 and middle:
                breakdown.append(
                    {
                        "signal": "bollinger_bands",
                        "effect": 0.0,
                        "detail": f"Bollinger band width ratio: {round(band_width / middle, 4)}.",
                    }
                )

        return score, breakdown

    def _score_fundamentals(
        self,
        fundamentals: dict[str, Any],
    ) -> tuple[float, list[dict[str, Any]]]:
        score = 0.0
        breakdown: list[dict[str, Any]] = []

        valuation = fundamentals.get("valuation")
        if valuation == "undervalued":
            score += 0.15
            breakdown.append({"signal": "fundamentals", "effect": 0.15, "detail": "Valuation profile appears undervalued."})
        elif valuation == "overvalued":
            score -= 0.15
            breakdown.append({"signal": "fundamentals", "effect": -0.15, "detail": "Valuation profile appears overvalued."})

        revenue_growth = fundamentals.get("revenue_growth")
        if isinstance(revenue_growth, (int, float)):
            if revenue_growth > 0.10:
                score += 0.10
                breakdown.append({"signal": "revenue_growth", "effect": 0.10, "detail": "Revenue growth is strong."})
            elif revenue_growth < 0:
                score -= 0.10
                breakdown.append({"signal": "revenue_growth", "effect": -0.10, "detail": "Revenue growth is negative."})

        debt_to_equity = fundamentals.get("debt_to_equity")
        if isinstance(debt_to_equity, (int, float)) and debt_to_equity > 1.5:
            score -= 0.05
            breakdown.append({"signal": "debt_to_equity", "effect": -0.05, "detail": "Leverage is elevated."})

        return score, breakdown

    def _score_sentiment(self, sentiment: dict[str, Any]) -> tuple[float, list[dict[str, Any]]]:
        score = 0.0
        breakdown: list[dict[str, Any]] = []

        sentiment_score = sentiment.get("score")
        if isinstance(sentiment_score, (int, float)):
            bounded = max(min(float(sentiment_score), 1.0), -1.0)
            effect = round(bounded * 0.15, 4)
            score += effect
            breakdown.append(
                {
                    "signal": "sentiment",
                    "effect": effect,
                    "detail": "Sentiment contributes a bounded secondary signal.",
                }
            )

        return score, breakdown

    def _score_prediction(self, prediction: dict[str, Any]) -> tuple[float, list[dict[str, Any]]]:
        score = 0.0
        breakdown: list[dict[str, Any]] = []

        direction = prediction.get("direction")
        confidence = prediction.get("confidence")
        if direction in {"UP", "DOWN"} and isinstance(confidence, (int, float)):
            bounded_confidence = min(max(float(confidence), 0.0), 1.0)
            effect = bounded_confidence * 0.12
            effect = effect if direction == "UP" else -effect
            score += effect
            breakdown.append(
                {
                    "signal": "ml_prediction",
                    "effect": round(effect, 4),
                    "detail": "ML prediction contributes a capped auxiliary signal.",
                }
            )

        return score, breakdown

    def _derive_risk_level(
        self,
        *,
        score: float,
        indicators: dict[str, Any],
        sentiment: dict[str, Any],
        prediction: dict[str, Any],
    ) -> str:
        disagreement = 0
        trend_bias = ((indicators.get("trend") or {}).get("bias"))
        sentiment_score = sentiment.get("score")
        prediction_direction = prediction.get("direction")

        if trend_bias == "bullish" and prediction_direction == "DOWN":
            disagreement += 1
        if trend_bias == "bearish" and prediction_direction == "UP":
            disagreement += 1
        if isinstance(sentiment_score, (int, float)):
            if score > 0 and sentiment_score < -0.4:
                disagreement += 1
            if score < 0 and sentiment_score > 0.4:
                disagreement += 1

        if abs(score) < 0.20 or disagreement >= 2:
            return "high"
        if abs(score) < 0.40 or disagreement == 1:
            return "medium"
        return "low"

    def _generate_llm_explanation(
        self,
        *,
        state: StockAnalysisState,
        decision: dict[str, Any],
        llm,
    ) -> dict[str, Any]:
        system_prompt = (
            "You are a stock analysis explainer. The deterministic decision is final. "
            "Do not change action, confidence, or risk_level. Return strict JSON with keys: "
            "reasoning, signal_breakdown, risk_flags. reasoning must be one concise paragraph. "
            "signal_breakdown and risk_flags must be arrays of short strings. No markdown."
        )
        user_prompt = json.dumps(
            {
                "symbol": state["symbol"],
                "final_decision_locked": {
                    "action": decision["action"],
                    "confidence": decision["confidence"],
                    "risk_level": decision["risk_level"],
                    "score": decision["score"],
                },
                "indicators": state.get("indicators", {}),
                "fundamentals": state.get("fundamentals", {}),
                "sentiment": state.get("sentiment", {}),
                "prediction": state.get("prediction", {}),
                "deterministic_breakdown": decision["breakdown"],
                "rules": {
                    "prediction_is_not_final_decision": True,
                    "deterministic_logic_dominates": True,
                    "ml_cannot_override_other_signals": True,
                },
            }
        )

        response = llm.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
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
            else "Deterministic scoring dominated the outcome; the explanation layer fell back to a default summary.",
            "signal_breakdown": signal_breakdown if isinstance(signal_breakdown, list) else [],
            "risk_flags": risk_flags if isinstance(risk_flags, list) else [],
        }
