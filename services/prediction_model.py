"""Local PyTorch prediction integration.

Prediction is an auxiliary signal only. It must never be treated as the final
trading decision.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from threading import Lock
from typing import Any, ClassVar

import pandas as pd
import torch
from torch import nn

from graph.state import StockAnalysisState
from services.config import Settings

FEATURE_COLUMNS: tuple[str, ...] = (
    "returns",
    "high_low_spread",
    "open_close_spread",
    "volume_change",
    "close_zscore",
)


@dataclass(frozen=True, slots=True)
class PredictionResult:
    direction: str
    confidence: float
    raw: dict[str, Any]
    signal_type: str = "ml_prediction"
    is_final_decision: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["confidence"] = round(float(payload["confidence"]), 4)
        return payload


class SimpleTrendModel(nn.Module):
    """Fallback architecture definition for loading a local state dict."""

    def __init__(self, input_size: int = len(FEATURE_COLUMNS), hidden_size: int = 32) -> None:
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            batch_first=True,
        )
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
    """Loads a local `.pt` model once and exposes deterministic inference."""

    _model_cache: ClassVar[dict[Path, nn.Module]] = {}
    _cache_lock: ClassVar[Lock] = Lock()

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.model_path = Path(settings.prediction_model_path)
        self.device = torch.device("cpu")

    def predict_from_state(self, state: StockAnalysisState) -> dict[str, Any]:
        frame = pd.DataFrame(state["price_data"])
        return self.predict(frame=frame, symbol=state.get("symbol"))

    def predict(self, *, frame: pd.DataFrame, symbol: str | None = None) -> dict[str, Any]:
        if frame.empty:
            raise ValueError("prediction model received empty price data")

        features = self._build_features(frame)
        if len(features) < self.settings.prediction_sequence_length:
            raise ValueError("not enough data points for prediction model")

        sequence = features.tail(self.settings.prediction_sequence_length)
        tensor = torch.tensor(sequence.values, dtype=torch.float32).unsqueeze(0)
        model = self._get_or_load_model()

        if model is None:
            return self._build_fallback_result(
                sequence=sequence,
                symbol=symbol,
            ).to_dict()

        probabilities = self._run_inference(model=model, tensor=tensor)
        result = self._build_prediction_result(
            probabilities=probabilities,
            symbol=symbol,
            sequence_length=len(sequence),
        )
        return result.to_dict()

    def _get_or_load_model(self) -> nn.Module | None:
        if not self.model_path.exists():
            return None

        with self._cache_lock:
            cached = self._model_cache.get(self.model_path)
            if cached is not None:
                return cached

            loaded = torch.load(self.model_path, map_location=self.device)
            if isinstance(loaded, nn.Module):
                model = loaded
            elif isinstance(loaded, dict):
                model = SimpleTrendModel()
                model.load_state_dict(loaded)
            else:
                raise ValueError("unsupported PyTorch artifact format")

            model.eval()
            self._model_cache[self.model_path] = model
            return model

    def _run_inference(self, *, model: nn.Module, tensor: torch.Tensor) -> dict[str, float]:
        with torch.inference_mode():
            logits = model(tensor.to(self.device))
            probabilities = torch.softmax(logits, dim=-1).squeeze(0).cpu()

        return {
            "DOWN": float(probabilities[0].item()),
            "UP": float(probabilities[1].item()),
        }

    def _build_prediction_result(
        self,
        *,
        probabilities: dict[str, float],
        symbol: str | None,
        sequence_length: int,
    ) -> PredictionResult:
        direction = "UP" if probabilities["UP"] >= probabilities["DOWN"] else "DOWN"
        confidence = max(probabilities.values())
        margin = abs(probabilities["UP"] - probabilities["DOWN"])

        return PredictionResult(
            direction=direction,
            confidence=confidence,
            raw={
                "status": "ok",
                "symbol": symbol,
                "model_path": str(self.model_path),
                "sequence_length": sequence_length,
                "probabilities": {
                    label: round(value, 4) for label, value in probabilities.items()
                },
                "margin": round(margin, 4),
                "feature_columns": list(FEATURE_COLUMNS),
                "note": "Prediction is an ML signal, not the final decision.",
            },
        )

    def _build_fallback_result(
        self,
        *,
        sequence: pd.DataFrame,
        symbol: str | None,
    ) -> PredictionResult:
        average_return = float(sequence["returns"].mean())
        direction = "UP" if average_return >= 0 else "DOWN"
        confidence = min(abs(average_return) * 20, 0.55)

        return PredictionResult(
            direction=direction,
            confidence=confidence,
            raw={
                "status": "fallback",
                "symbol": symbol,
                "model_path": str(self.model_path),
                "reason": "model artifact not found",
                "feature_columns": list(FEATURE_COLUMNS),
                "heuristic_average_return": round(average_return, 6),
                "note": "Fallback output is still only an auxiliary signal.",
            },
        )

    @staticmethod
    def _build_features(frame: pd.DataFrame) -> pd.DataFrame:
        ordered = frame.copy()
        ordered["timestamp"] = pd.to_datetime(ordered["timestamp"], utc=True)
        ordered = ordered.sort_values("timestamp").reset_index(drop=True)

        ordered["returns"] = ordered["close"].pct_change().fillna(0.0)
        ordered["high_low_spread"] = (
            (ordered["high"] - ordered["low"]) / ordered["close"]
        ).replace([float("inf"), float("-inf")], 0.0).fillna(0.0)
        ordered["open_close_spread"] = (
            (ordered["close"] - ordered["open"]) / ordered["open"]
        ).replace([float("inf"), float("-inf")], 0.0).fillna(0.0)
        ordered["volume_change"] = ordered["volume"].pct_change().replace(
            [float("inf"), float("-inf")], 0.0
        ).fillna(0.0)
        rolling_mean = ordered["close"].rolling(20, min_periods=20).mean()
        rolling_std = ordered["close"].rolling(20, min_periods=20).std()
        ordered["close_zscore"] = (
            (ordered["close"] - rolling_mean) / rolling_std
        ).replace([float("inf"), float("-inf")], 0.0).fillna(0.0)

        # TODO: expand feature engineering with regime features, volatility buckets, and market breadth.
        # TODO: add normalization metadata that matches training-time transforms exactly.
        # TODO: support ensemble models once multiple local artifacts are versioned and validated.
        # TODO: evaluate online learning separately from live inference; do not mutate weights in-process.
        return ordered.loc[:, FEATURE_COLUMNS].astype("float32")
