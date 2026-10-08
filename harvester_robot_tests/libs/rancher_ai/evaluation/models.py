"""Independent configuration, results and errors for response evaluation.
"""
import math
import os
from dataclasses import asdict, dataclass, field
from typing import Mapping, Optional


class EvaluationError(Exception):
    """Evaluation could not produce a valid judgment; no score is fabricated."""


class EvaluationConfigError(EvaluationError):
    """Missing or invalid configuration or evaluation input."""


class EvaluationProviderError(EvaluationError):
    """SDK loading or judge provider failure."""


class EvaluationTimeoutError(EvaluationProviderError):
    """DeepEval's soft timeout or the provider's HTTP timeout expired."""


class EvaluationResponseError(EvaluationProviderError):
    """The judge did not produce a valid score and reason."""


@dataclass(frozen=True)
class EvaluationConfig:
    """Environment access is explicit and does not load credential files.
    """
    api_key: str = field(repr=False)
    model_name: str = "gemini-3.6-flash"
    threshold: float = 0.8
    timeout: float = 120.0

    def __post_init__(self) -> None:
        for name, value in (
            ("GOOGLE_API_KEY", self.api_key),
            ("GEMINI_MODEL_NAME", self.model_name),
        ):
            if (
                not isinstance(value, str)
                or not value
                or any(char.isspace() or ord(char) < 0x20 for char in value)
            ):
                raise EvaluationConfigError(f"{name} must be nonempty without whitespace")

        if (
            isinstance(self.threshold, bool)
            or not isinstance(self.threshold, (int, float))
            or not math.isfinite(self.threshold)
            or not 0 <= self.threshold <= 1
        ):
            raise EvaluationConfigError("AI_EVAL_THRESHOLD must be a finite number in [0, 1]")

        if (
            isinstance(self.timeout, bool)
            or not isinstance(self.timeout, (int, float))
            or not math.isfinite(self.timeout)
            or self.timeout <= 0
        ):
            raise EvaluationConfigError("AI_EVAL_TIMEOUT must be a finite positive number")

    @classmethod
    def from_env(cls, environ: Optional[Mapping[str, str]] = None) -> "EvaluationConfig":
        env = os.environ if environ is None else environ

        key = env.get("GOOGLE_API_KEY", "")
        if not isinstance(key, str) or not key.strip():
            raise EvaluationConfigError("Missing configuration: GOOGLE_API_KEY")

        numbers = {}
        for name, default in (
            ("AI_EVAL_THRESHOLD", cls.threshold), ("AI_EVAL_TIMEOUT", cls.timeout)
        ):
            try:
                numbers[name] = float(env.get(name, default))
            except (ValueError, TypeError):
                raise EvaluationConfigError(f"{name} has an invalid numeric value") from None

        return cls(
            api_key=key,
            model_name=env.get("GEMINI_MODEL_NAME", cls.model_name),
            threshold=numbers["AI_EVAL_THRESHOLD"],
            timeout=numbers["AI_EVAL_TIMEOUT"],
        )


@dataclass(frozen=True)
class EvaluationResult:
    """A semantic judgment, not independent evidence of resource persistence."""

    score: float
    threshold: float
    passed: bool
    reason: str = field(repr=False)
    metric_name: str
    judge_model: str
    rubric_version: str
    elapsed_seconds: float

    def to_dict(self) -> dict:
        return asdict(self)
