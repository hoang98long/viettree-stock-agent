"""Analysis endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from apps.api.dependencies import get_analysis_service
from apps.api.schemas import AnalysisRequest, AnalysisResponse
from services.analysis_service import AnalysisService

router = APIRouter(tags=["analysis"])


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_stock(
    payload: AnalysisRequest,
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> AnalysisResponse:
    try:
        result = await analysis_service.analyze_symbol(
            symbol=payload.symbol,
            lookback_days=payload.lookback_days,
            include_fundamentals=payload.include_fundamentals,
            include_sentiment=payload.include_sentiment,
            include_prediction=payload.include_prediction,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return AnalysisResponse.model_validate(result)
