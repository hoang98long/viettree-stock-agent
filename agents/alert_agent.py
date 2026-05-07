"""Alert generation agent."""

from graph.state import StockAnalysisState


class AlertAgent:
    """Derives actionable alerts from the final decision state."""

    def __call__(self, state: StockAnalysisState) -> StockAnalysisState:
        decision = state.get("decision") or {}
        indicators = state.get("indicators") or {}
        sentiment = state.get("sentiment") or {}
        alerts: list[dict[str, object]] = []

        action = decision.get("action", "HOLD")
        confidence = float(decision.get("confidence", 0.0))
        if action != "HOLD" and confidence >= 0.7:
            alerts.append(
                {
                    "type": "trade_signal",
                    "severity": "high",
                    "message": f"{state['symbol']} flagged as {action}",
                    "confidence": confidence,
                }
            )

        rsi = indicators.get("rsi_14")
        if isinstance(rsi, (int, float)):
            if rsi >= 70:
                alerts.append(
                    {
                        "type": "technical",
                        "severity": "medium",
                        "message": "Overbought RSI condition detected.",
                    }
                )
            elif rsi <= 30:
                alerts.append(
                    {
                        "type": "technical",
                        "severity": "medium",
                        "message": "Oversold RSI condition detected.",
                    }
                )

        sentiment_score = sentiment.get("score")
        if isinstance(sentiment_score, (int, float)) and abs(sentiment_score) >= 0.7:
            alerts.append(
                {
                    "type": "sentiment",
                    "severity": "medium",
                    "message": "Material sentiment skew detected.",
                    "score": sentiment_score,
                }
            )

        return {"alerts": alerts}
