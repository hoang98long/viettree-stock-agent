"""Prediction agent backed by a local PyTorch model."""

from services.prediction_model import PredictionModelService

from graph.state import StockAnalysisState


class PredictionAgent:
    """Runs the local ML model to emit a directional signal."""

    def __init__(self, prediction_service: PredictionModelService) -> None:
        self.prediction_service = prediction_service

    def __call__(self, state: StockAnalysisState) -> StockAnalysisState:
        if not state["metadata"].get("include_prediction", True):
            return {"prediction": {"status": "skipped"}}

        prediction = self.prediction_service.predict_from_state(state)
        return {"prediction": prediction}
