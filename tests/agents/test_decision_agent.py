from __future__ import annotations

from agents.decision_agent import DecisionAgent
from graph.state import StockAnalysisState


def test_decision_agent_combines_signals_with_deterministic_dominance(
    decision_agent: DecisionAgent,
) -> None:
    state: StockAnalysisState = {
        "symbol": "AAPL",
        "indicators": {
            "rsi": {"period": 14, "value": 32.0},
            "macd": {"histogram": 1.2},
            "bollinger_bands": {"upper": 120.0, "middle": 100.0, "lower": 80.0},
            "trend": {"bias": "bullish"},
        },
        "fundamentals": {
            "valuation": "undervalued",
            "revenue_growth": 0.16,
            "debt_to_equity": 0.8,
        },
        "sentiment": {"score": 0.3},
        "prediction": {
            "direction": "DOWN",
            "confidence": 0.95,
            "signal_type": "ml_prediction",
            "is_final_decision": False,
        },
        "metadata": {},
    }

    result = decision_agent(state)
    decision = result["decision"]

    assert decision["action"] == "BUY"
    assert decision["confidence"] > 0
    assert decision["risk_level"] in {"low", "medium", "high"}
    assert decision["model_role"] == "explanation_only"
    assert any(item["signal"] == "ml_prediction" for item in decision["deterministic_breakdown"])


def test_decision_agent_uses_mock_llm_output(decision_agent: DecisionAgent) -> None:
    state: StockAnalysisState = {
        "symbol": "MSFT",
        "indicators": {"rsi": {"value": 50}, "macd": {"histogram": 0.0}, "trend": {"bias": "neutral"}},
        "fundamentals": {},
        "sentiment": {"score": 0.0},
        "prediction": {},
        "metadata": {},
    }

    result = decision_agent(state)
    assert "Deterministic signals lean bullish" in result["decision"]["reasoning"]
    assert isinstance(result["decision"]["signal_breakdown"], list)
