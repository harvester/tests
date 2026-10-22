"""Independent configuration, results and errors for response evaluation.
"""
import math
import os
from dataclasses import asdict, dataclass, field
from typing import Mapping, Optional
from urllib.parse import urlsplit

from ..models import _get_config_value


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
    """Robot/environment access is explicit and does not load credential files.
    """
    api_key: str = field(default="", repr=False)
    model_name: str = "gemini-3.6-flash"
    threshold: float = 0.8
    timeout: float = 120.0
    provider: str = "gemini"
    base_url: Optional[str] = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self.provider not in ("gemini", "ollama"):
            raise EvaluationConfigError("Evaluation provider must be gemini or ollama")
        fields = [("OLLAMA_MODEL" if self.provider == "ollama" else "GEMINI_MODEL",
                   self.model_name)]
        if self.provider == "gemini":
            fields.append(("GEMINI_API_KEY", self.api_key))
        else:
            fields.append(("OLLAMA_URL", self.base_url))
        for name, value in fields:
            if (
                not isinstance(value, str)
                or not value
                or any(char.isspace() or ord(char) < 0x20 for char in value)
            ):
                raise EvaluationConfigError(f"{name} must be nonempty without whitespace")

        if self.provider == "ollama":
            try:
                url = urlsplit(self.base_url)
                valid_url = (
                    url.scheme in ("http", "https") and bool(url.hostname)
                    and url.username is None and url.password is None
                    and not url.query and not url.fragment
                    and "?" not in self.base_url and "#" not in self.base_url
                    and (url.port is None or 1 <= url.port <= 65535)
                )
            except ValueError:
                valid_url = False
            if not valid_url:
                raise EvaluationConfigError(
                    "OLLAMA_URL must be an HTTP(S) URL without credentials, query or fragment"
                )

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
        """Resolve Robot settings before environment values, then select the provider.
        """
        env = os.environ if environ is None else environ

        selected = None
        for provider, first, second in (
            ("ollama", "OLLAMA_URL", "OLLAMA_MODEL"),
            ("gemini", "GEMINI_API_KEY", "GEMINI_MODEL"),
        ):
            first_value = _get_config_value(first, env, "")
            second_value = _get_config_value(second, env, "")
            if (isinstance(first_value, str) and isinstance(second_value, str)
                    and first_value.strip() and second_value.strip()):
                selected = provider, (first_value, second_value)
                break
        if selected is None:
            raise EvaluationConfigError(
                "Missing configuration: OLLAMA_URL and OLLAMA_MODEL, "
                "or GEMINI_API_KEY and GEMINI_MODEL are required"
            )

        numbers = {}
        for name, default in (
            ("AI_EVAL_THRESHOLD", cls.threshold), ("AI_EVAL_TIMEOUT", cls.timeout)
        ):
            value = _get_config_value(name, env, default)
            try:
                if isinstance(value, bool) or not isinstance(value, (str, int, float)):
                    raise ValueError
                numbers[name] = float(value)
            except (ValueError, TypeError, OverflowError):
                raise EvaluationConfigError(f"{name} has an invalid numeric value") from None

        provider, (credential, model_name) = selected
        return cls(
            api_key=credential if provider == "gemini" else "",
            model_name=model_name,
            threshold=numbers["AI_EVAL_THRESHOLD"],
            timeout=numbers["AI_EVAL_TIMEOUT"],
            provider=provider,
            base_url=credential if provider == "ollama" else None,
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
