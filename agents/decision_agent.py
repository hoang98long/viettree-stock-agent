"""Decision synthesis agent."""

from services.decision_parser import DecisionEngine
from services.llm import OllamaClientFactory

from graph.state import StockAnalysisState


class DecisionAgent:
    """Combines deterministic signals with constrained LLM reasoning."""

    def __init__(
        self,
        llm_factory: OllamaClientFactory,
        decision_engine: DecisionEngine,
    ) -> None:
        self.llm_factory = llm_factory
        self.decision_engine = decision_engine

    def __call__(self, state: StockAnalysisState) -> StockAnalysisState:
        llm = self.llm_factory.build_reasoning_llm()
        decision = self.decision_engine.decide(state=state, llm=llm)
        return {"decision": decision}
