"""Application-specific exceptions."""

from __future__ import annotations


class ApplicationError(Exception):
    """Base application exception."""


class ValidationError(ApplicationError):
    """Input or state validation failure."""


class ExternalDependencyError(ApplicationError):
    """Transient or permanent external dependency failure."""


class MarketDataUnavailableError(ExternalDependencyError):
    """Market data provider returned no usable data."""


class ModelInferenceError(ApplicationError):
    """Prediction model loading or inference failed."""
