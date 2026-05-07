"""LangGraph orchestration builder."""

from langgraph.graph import END, StateGraph

from agents.alert_agent import AlertAgent
from agents.data_agent import DataAgent
from agents.decision_agent import DecisionAgent
from agents.fundamental_agent import FundamentalAgent
from agents.prediction_agent import PredictionAgent
from agents.sentiment_agent import SentimentAgent
from agents.technical_agent import TechnicalAgent
from graph.state import StockAnalysisState


def build_analysis_graph(
    *,
    data_agent: DataAgent,
    technical_agent: TechnicalAgent,
    fundamental_agent: FundamentalAgent,
    sentiment_agent: SentimentAgent,
    prediction_agent: PredictionAgent,
    decision_agent: DecisionAgent,
    alert_agent: AlertAgent,
):
    workflow = StateGraph(StockAnalysisState)

    workflow.add_node("data_agent", data_agent)
    workflow.add_node("technical_agent", technical_agent)
    workflow.add_node("fundamental_agent", fundamental_agent)
    workflow.add_node("sentiment_agent", sentiment_agent)
    workflow.add_node("prediction_agent", prediction_agent)
    workflow.add_node("decision_agent", decision_agent)
    workflow.add_node("alert_agent", alert_agent)

    workflow.set_entry_point("data_agent")
    workflow.add_edge("data_agent", "technical_agent")
    workflow.add_edge("data_agent", "fundamental_agent")
    workflow.add_edge("data_agent", "sentiment_agent")
    workflow.add_edge("data_agent", "prediction_agent")
    workflow.add_edge("technical_agent", "decision_agent")
    workflow.add_edge("fundamental_agent", "decision_agent")
    workflow.add_edge("sentiment_agent", "decision_agent")
    workflow.add_edge("prediction_agent", "decision_agent")
    workflow.add_edge("decision_agent", "alert_agent")
    workflow.add_edge("alert_agent", END)

    return workflow.compile()
