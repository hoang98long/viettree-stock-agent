"""Dependency wiring for API handlers."""

from functools import lru_cache

from services.analysis_service import AnalysisService
from services.config import Settings, get_settings
from services.runtime import build_runtime


@lru_cache
def get_analysis_service() -> AnalysisService:
    return build_runtime()


def get_settings_dependency() -> Settings:
    return get_settings()
