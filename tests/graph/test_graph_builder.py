from __future__ import annotations

from graph.state import StockAnalysisState


def test_analysis_graph_invokes_parallel_flow_and_returns_structured_state(
    analysis_graph,
) -> None:
    state: StockAnalysisState = {
        "symbol": "AAPL",
        "price_data": {},
        "indicators": {},
        "fundamentals": {},
        "sentiment": {},
        "prediction": {},
        "decision": {},
        "alerts": [],
        "metadata": {
            "lookback_days": 180,
            "include_fundamentals": True,
            "include_sentiment": True,
            "include_prediction": True,
        },
    }

    result = analysis_graph.invoke(state)

    assert result["symbol"] == "AAPL"
    assert "indicators" in result
    assert "fundamentals" in result
    assert "sentiment" in result
    assert "prediction" in result
    assert "decision" in result
    assert "alerts" in result


def test_analysis_graph_respects_prediction_toggle(
    analysis_graph,
) -> None:
    state: StockAnalysisState = {
        "symbol": "AAPL",
        "price_data": {},
        "indicators": {},
        "fundamentals": {},
        "sentiment": {},
        "prediction": {},
        "decision": {},
        "alerts": [],
        "metadata": {
            "lookback_days": 180,
            "include_fundamentals": True,
            "include_sentiment": True,
            "include_prediction": False,
        },
    }

    result = analysis_graph.invoke(state)
    assert result["prediction"]["status"] == "skipped"
