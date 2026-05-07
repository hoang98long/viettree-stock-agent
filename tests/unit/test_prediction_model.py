from __future__ import annotations

import pandas as pd

from services.prediction_model import PredictionModelService


def test_prediction_service_returns_structured_fallback(
    prediction_service: PredictionModelService,
    sample_price_frame: pd.DataFrame,
) -> None:
    result = prediction_service.predict(frame=sample_price_frame, symbol="AAPL")

    assert result["direction"] in {"UP", "DOWN"}
    assert 0.0 <= result["confidence"] <= 1.0
    assert result["signal_type"] == "ml_prediction"
    assert result["is_final_decision"] is False
    assert result["raw"]["status"] == "fallback"


def test_prediction_service_feature_generation_is_deterministic(
    prediction_service: PredictionModelService,
    sample_price_frame: pd.DataFrame,
) -> None:
    features_one = prediction_service._build_features(sample_price_frame)
    features_two = prediction_service._build_features(sample_price_frame)

    assert list(features_one.columns) == list(features_two.columns)
    assert features_one.equals(features_two)
