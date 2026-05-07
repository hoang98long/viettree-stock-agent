"""Local PyTorch prediction service."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import torch
from torch import nn

from graph.state import StockAnalysisState
from services.config import Settings


class SimpleTrendModel(nn.Module):
    """Fallback architecture definition for loading a local state dict."""

    def __init__(self, input_size: int = 5, hidden_size: int = 32) -> None:
        super().__init__()
        self.lstm = nn.LSTM(input_size=input_size, hidden_size=hidden_size, batch_first=True)
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size, 16),
            nn.ReLU(),
            nn.Linear(16, 2),
        )

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        sequence, _ = self.lstm(inputs)
        last_step = sequence[:, -1, :]
        return self.classifier(last_step)


class PredictionModelService:
    """Loads a local `.pt` artifact and produces an auxiliary signal."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.model_path = Path(settings.prediction_model_path)
        self.device = torch.device("cpu")
        self._model: nn.Module | None = None

    def predict_from_state(self, state: StockAnalysisState) -> dict[str, Any]:
        frame = pd.DataFrame(state["price_data"])
        if frame.empty:
            raise ValueError("prediction agent received empty price data")

        features = self._build_features(frame)
        if len(features) < self.settings.prediction_sequence_length:
            raise ValueError("not enough data points for prediction model")

        sequence = features.tail(self.settings.prediction_sequence_length)
        tensor = torch.tensor(sequence.values, dtype=torch.float32).unsqueeze(0)

        model = self._load_model()
        if model is None:
            return {
                "direction": "DOWN" if sequence["returns"].mean() < 0 else "UP",
                "confidence": round(min(abs(sequence["returns"].mean()) * 20, 0.55), 4),
                "raw": {
                    "status": "fallback",
                    "reason": f"model file not found at {self.model_path}",
                },
            }

        model.eval()
        with torch.no_grad():
            logits = model(tensor.to(self.device))
            probabilities = torch.softmax(logits, dim=-1).squeeze(0).cpu()

        down_confidence = float(probabilities[0].item())
        up_confidence = float(probabilities[1].item())
        direction = "UP" if up_confidence >= down_confidence else "DOWN"
        confidence = max(up_confidence, down_confidence)
        return {
            "direction": direction,
            "confidence": round(confidence, 4),
            "raw": {
                "probabilities": {
                    "DOWN": round(down_confidence, 4),
                    "UP": round(up_confidence, 4),
                }
            },
        }

    def _load_model(self) -> nn.Module | None:
        if self._model is not None:
            return self._model
        if not self.model_path.exists():
            return None

        loaded = torch.load(self.model_path, map_location=self.device)
        if isinstance(loaded, nn.Module):
            self._model = loaded
            return self._model

        model = SimpleTrendModel()
        if isinstance(loaded, dict):
            model.load_state_dict(loaded)
            self._model = model
            return self._model

        raise ValueError("unsupported PyTorch artifact format")

    @staticmethod
    def _build_features(frame: pd.DataFrame) -> pd.DataFrame:
        ordered = frame.copy()
        ordered["timestamp"] = pd.to_datetime(ordered["timestamp"], utc=True)
        ordered = ordered.sort_values("timestamp")
        ordered["returns"] = ordered["close"].pct_change().fillna(0.0)
        ordered["high_low_spread"] = (
            (ordered["high"] - ordered["low"]) / ordered["close"]
        ).fillna(0.0)
        ordered["open_close_spread"] = (
            (ordered["close"] - ordered["open"]) / ordered["open"]
        ).fillna(0.0)
        ordered["volume_change"] = ordered["volume"].pct_change().replace(
            [float("inf"), float("-inf")], 0.0
        ).fillna(0.0)
        ordered["close_zscore"] = (
            (ordered["close"] - ordered["close"].rolling(20).mean())
            / ordered["close"].rolling(20).std()
        ).replace([float("inf"), float("-inf")], 0.0).fillna(0.0)
        return ordered[
            [
                "returns",
                "high_low_spread",
                "open_close_spread",
                "volume_change",
                "close_zscore",
            ]
        ]
