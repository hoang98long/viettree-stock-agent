"""Prediction agent backed by a local PyTorch model."""

from graph.state import StockAnalysisState
from services.prediction_model import PredictionModelService


class PredictionAgent:
    """Runs local ML inference and returns a structured signal only."""

    def __init__(self, prediction_service: PredictionModelService) -> None:
        self.prediction_service = prediction_service

    def __call__(self, state: StockAnalysisState) -> StockAnalysisState:
        if not state["metadata"].get("include_prediction", True):
            return {
                "prediction": {
                    "status": "skipped",
                    "signal_type": "ml_prediction",
                    "is_final_decision": False,
                    "note": "Prediction is disabled for this run.",
                }
            }

        prediction = self.prediction_service.predict_from_state(state)
        return {"prediction": prediction}
