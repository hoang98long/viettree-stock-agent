"""LangGraph orchestration builder for stock analysis."""

from __future__ import annotations

from typing import Final

from langgraph.graph import END, START, CompiledStateGraph, StateGraph

from agents.alert_agent import AlertAgent
from agents.data_agent import DataAgent
from agents.decision_agent import DecisionAgent
from agents.fundamental_agent import FundamentalAgent
from agents.prediction_agent import PredictionAgent
from agents.sentiment_agent import SentimentAgent
from agents.technical_agent import TechnicalAgent
from graph.state import StockAnalysisState

DATA_AGENT: Final[str] = "data_agent"
TECHNICAL_AGENT: Final[str] = "technical_agent"
FUNDAMENTAL_AGENT: Final[str] = "fundamental_agent"
SENTIMENT_AGENT: Final[str] = "sentiment_agent"
PREDICTION_AGENT: Final[str] = "prediction_agent"
DECISION_AGENT: Final[str] = "decision_agent"
ALERT_AGENT: Final[str] = "alert_agent"

PARALLEL_ANALYSIS_NODES: Final[tuple[str, ...]] = (
    TECHNICAL_AGENT,
    FUNDAMENTAL_AGENT,
    SENTIMENT_AGENT,
    PREDICTION_AGENT,
)


def build_analysis_graph(
    *,
    data_agent: DataAgent,
    technical_agent: TechnicalAgent,
    fundamental_agent: FundamentalAgent,
    sentiment_agent: SentimentAgent,
    prediction_agent: PredictionAgent,
    decision_agent: DecisionAgent,
    alert_agent: AlertAgent,
) -> CompiledStateGraph:
    """Build the stock analysis graph.

    The topology is intentionally explicit:
    START -> data_agent -> parallel analysis branches -> decision_agent -> alert_agent -> END
    """

    workflow = StateGraph(StockAnalysisState)
    _register_nodes(
        workflow=workflow,
        data_agent=data_agent,
        technical_agent=technical_agent,
        fundamental_agent=fundamental_agent,
        sentiment_agent=sentiment_agent,
        prediction_agent=prediction_agent,
        decision_agent=decision_agent,
        alert_agent=alert_agent,
    )
    _register_edges(workflow)

    # TODO: attach node-level retry policies once agent-specific retry semantics are finalized.
    # TODO: add memory-aware routing when conversation or portfolio context becomes part of state.
    # TODO: add self-reflection loop only after bounded validation criteria are defined.
    # TODO: add backtesting branch wiring that can replay historical runs without touching live paths.
    return workflow.compile()


def _register_nodes(
    *,
    workflow: StateGraph,
    data_agent: DataAgent,
    technical_agent: TechnicalAgent,
    fundamental_agent: FundamentalAgent,
    sentiment_agent: SentimentAgent,
    prediction_agent: PredictionAgent,
    decision_agent: DecisionAgent,
    alert_agent: AlertAgent,
) -> None:
    workflow.add_node(DATA_AGENT, data_agent)
    workflow.add_node(TECHNICAL_AGENT, technical_agent)
    workflow.add_node(FUNDAMENTAL_AGENT, fundamental_agent)
    workflow.add_node(SENTIMENT_AGENT, sentiment_agent)
    workflow.add_node(PREDICTION_AGENT, prediction_agent)
    workflow.add_node(DECISION_AGENT, decision_agent)
    workflow.add_node(ALERT_AGENT, alert_agent)


def _register_edges(workflow: StateGraph) -> None:
    workflow.add_edge(START, DATA_AGENT)

    for node_name in PARALLEL_ANALYSIS_NODES:
        workflow.add_edge(DATA_AGENT, node_name)
        workflow.add_edge(node_name, DECISION_AGENT)

    workflow.add_edge(DECISION_AGENT, ALERT_AGENT)
    workflow.add_edge(ALERT_AGENT, END)

    # TODO: add conditional routing from decision_agent for hold-only paths, escalations, or human review.
