"""Opt-in response evaluation; importing this package does not load any SDK."""

from .evaluator import ResponseEvaluator
from .models import (
    EvaluationConfig,
    EvaluationConfigError,
    EvaluationError,
    EvaluationProviderError,
    EvaluationResponseError,
    EvaluationResult,
    EvaluationTimeoutError,
)
from .rubrics import DEFAULT_EVALUATION_STEPS, DEFAULT_RUBRIC_VERSION

__all__ = [
    "ResponseEvaluator", "EvaluationConfig", "EvaluationResult", "EvaluationError",
    "EvaluationConfigError", "EvaluationProviderError", "EvaluationResponseError",
    "EvaluationTimeoutError", "DEFAULT_EVALUATION_STEPS", "DEFAULT_RUBRIC_VERSION",
]
