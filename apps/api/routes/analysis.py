"""Analysis endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from apps.api.dependencies import get_analysis_service
from apps.api.schemas import AnalysisResponse, ErrorResponse
from services.analysis_service import AnalysisService

LOGGER = logging.getLogger(__name__)

router = APIRouter(tags=["analysis"])


@router.get(
    "/analyze/{symbol}",
    response_model=AnalysisResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
    },
)
async def analyze_stock(
    symbol: str = Path(..., min_length=1, max_length=12, description="Ticker symbol"),
    lookback_days: int = Query(default=180, ge=60, le=1000),
    include_fundamentals: bool = Query(default=True),
    include_sentiment: bool = Query(default=True),
    include_prediction: bool = Query(default=True),
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> AnalysisResponse:
    normalized_symbol = symbol.strip().upper()
    LOGGER.info(
        "analysis requested symbol=%s lookback_days=%s include_fundamentals=%s include_sentiment=%s include_prediction=%s",
        normalized_symbol,
        lookback_days,
        include_fundamentals,
        include_sentiment,
        include_prediction,
    )

    try:
        result = await analysis_service.analyze_symbol(
            symbol=normalized_symbol,
            lookback_days=lookback_days,
            include_fundamentals=include_fundamentals,
            include_sentiment=include_sentiment,
            include_prediction=include_prediction,
        )
    except ValueError as exc:
        LOGGER.warning("analysis rejected symbol=%s error=%s", normalized_symbol, exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        LOGGER.exception("analysis failed symbol=%s", normalized_symbol)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="internal server error",
        ) from exc

    LOGGER.info("analysis completed symbol=%s action=%s", normalized_symbol, result["decision"].get("action"))
    return AnalysisResponse.model_validate(result)
