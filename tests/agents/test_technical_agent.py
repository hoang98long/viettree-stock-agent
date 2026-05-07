from __future__ import annotations

from agents.technical_agent import TechnicalAgent
from services.indicator_service import TechnicalIndicatorService


def test_technical_agent_returns_nested_indicator_dictionary(
    serialized_price_data: dict[str, list],
) -> None:
    agent = TechnicalAgent(TechnicalIndicatorService())
    result = agent({"price_data": serialized_price_data})
    indicators = result["indicators"]

    assert indicators["status"] == "ok"
    assert "rsi" in indicators
    assert "macd" in indicators
    assert "bollinger_bands" in indicators
    assert "trend" in indicators


def test_technical_agent_requires_price_data() -> None:
    agent = TechnicalAgent(TechnicalIndicatorService())

    try:
        agent({"price_data": {}})
    except ValueError as exc:
        assert "price_data" in str(exc)
    else:
        raise AssertionError("technical agent should raise ValueError for empty price_data")
