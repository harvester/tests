"""Generic synchronous DeepEval/Gemini evaluation, independent of the AI client."""

import math
import os
import re
import time
from asyncio import TimeoutError as AsyncTimeoutError
from collections.abc import Sequence
from contextlib import suppress
from typing import Optional

from .models import (
    EvaluationConfig, EvaluationConfigError, EvaluationError,
    EvaluationProviderError, EvaluationResponseError, EvaluationResult,
    EvaluationTimeoutError,
)
from .rubrics import DEFAULT_EVALUATION_STEPS, DEFAULT_RUBRIC_VERSION


# Applied only at evaluation time, before SDK imports. These are process-wide
# DeepEval settings, not a sandbox or a way to undo earlier SDK import effects.
_SDK_ENV = {
    "DEEPEVAL_DISABLE_DOTENV": "1",
    "DEEPEVAL_DISABLE_LEGACY_KEYFILE": "1",
    "DEEPEVAL_TELEMETRY_OPT_OUT": "1",
    "DEEPEVAL_UPDATE_WARNING_OPT_IN": "0",
    "ENABLE_DEEPEVAL_CACHE": "0",
    "CONFIDENT_TRACE_SAMPLE_RATE": "0",
    "CONFIDENT_TRACE_FLUSH": "0",
    "CONFIDENT_TRACE_VERBOSE": "0",
    "DEEPEVAL_VERBOSE_MODE": "0",
    "DEEPEVAL_LOG_STACK_TRACES": "0",
    "DEEPEVAL_RETRY_BEFORE_LOG_LEVEL": "NOTSET",
    "DEEPEVAL_RETRY_AFTER_LOG_LEVEL": "NOTSET",
    "DEEPEVAL_RETRY_MAX_ATTEMPTS": "1",
    "DEEPEVAL_SDK_RETRY_PROVIDERS": '["google"]',
    "DEEPEVAL_DISABLE_TIMEOUTS": "0",
}
_MULTIMODAL_MARKER = re.compile(r"\[DEEPEVAL:(?:IMAGE|PDF):.*?\]")


def _validate_text(value: object, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise EvaluationConfigError(f"{name} must be a nonempty string")
    # DeepEval interprets these markers as files/URLs, even in a string answer.
    if _MULTIMODAL_MARKER.search(value):
        raise EvaluationConfigError(f"{name} must be plain text without DeepEval media markers")


def _redact(value: str, secrets: tuple[str, ...]) -> str:
    for secret in secrets:
        value = value.replace(secret, "[REDACTED]")
    return value


def _status_code(error: Exception) -> Optional[int]:
    for name in ("code", "status_code"):
        value = getattr(error, name, None)
        if isinstance(value, int) and not isinstance(value, bool) and 100 <= value < 600:
            return value
    return None


def _measure_once(
    config: EvaluationConfig,
    input: str,
    actual_output: str,
    expected_output: Optional[str],
    evaluation_steps: tuple[str, ...],
) -> tuple[object, object]:
    """Measure output by LLM-as-a-judge with ordinary SDK calls; no worker or generated criteria.

    Returns:
        (score, reason): score is a float in [0, 1], reason is a nonempty string.
    Raises:
        EvaluationError on any failure
    """
    import httpx
    from deepeval.metrics import GEval
    from deepeval.models import GeminiModel
    from deepeval.test_case import LLMTestCase, SingleTurnParams
    from google.genai.types import HttpOptions, HttpRetryOptions
    from tenacity import RetryError

    # GeminiModel.load_model() creates additional clients during generation.
    # A caller-owned sync transport gives those clients one explicit lifecycle.
    transport = httpx.Client()
    model = None
    try:
        model = GeminiModel(
            model=config.model_name,
            api_key=config.api_key,
            temperature=0,
            use_vertexai=False,
            vertexai=False,
            generation_kwargs={
                "automatic_function_calling": {"disable": True},
            },
            http_options=HttpOptions(
                timeout=max(1, math.ceil(config.timeout * 1000)),
                retry_options=HttpRetryOptions(attempts=1),
                httpx_client=transport,
            ),
        )
        params = [SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT]
        case_values = {"input": input, "actual_output": actual_output}
        if expected_output is not None:
            params.append(SingleTurnParams.EXPECTED_OUTPUT)
            case_values["expected_output"] = expected_output
        test_case = LLMTestCase(**case_values)
        metric = GEval(
            name="Rancher AI Response",
            evaluation_params=params,
            evaluation_steps=list(evaluation_steps),
            model=model,
            threshold=config.threshold,
            async_mode=False,
            strict_mode=False,
            verbose_mode=False,
        )
        metric.measure(test_case, _show_indicator=False)
        return metric.score, metric.reason
    except RetryError as error:
        cause = error.last_attempt.exception()
        if isinstance(cause, (TimeoutError, AsyncTimeoutError, httpx.TimeoutException)):
            raise EvaluationTimeoutError("Response evaluation timed out") from None
        if cause is None:
            raise EvaluationResponseError("Judge returned no valid response") from None
        raise cause from None
    except httpx.TimeoutException:
        raise EvaluationTimeoutError("Response evaluation timed out") from None
    finally:
        if model is not None:
            with suppress(Exception):
                model.model.close()
        with suppress(Exception):
            transport.close()


class ResponseEvaluator:
    """Evaluate prompt/answer consistency by LLM-as-a-judge
    """
    def __init__(self, config: Optional[EvaluationConfig] = None):
        self.config = config

    def evaluate_response(
        self,
        input: str,
        actual_output: str,
        expected_output: Optional[str] = None,
        evaluation_steps: Optional[Sequence[str]] = None,
    ) -> EvaluationResult:
        _validate_text(input, "input")
        _validate_text(actual_output, "actual_output")
        if expected_output is not None:
            _validate_text(expected_output, "expected_output")

        if evaluation_steps is None:
            steps = DEFAULT_EVALUATION_STEPS
            version = DEFAULT_RUBRIC_VERSION
        else:
            if (
                not isinstance(evaluation_steps, Sequence)
                or isinstance(evaluation_steps, (str, bytes))
                or not evaluation_steps
            ):
                raise EvaluationConfigError(
                    "evaluation_steps must be a nonempty sequence of strings"
                )
            for step in evaluation_steps:
                _validate_text(step, "evaluation_steps item")
            steps = tuple(evaluation_steps)
            version = "custom-v1"

        config = self.config if self.config is not None else EvaluationConfig.from_env()
        secrets = tuple(
            value for value in (config.api_key, os.environ.get("RANCHER_API_TOKEN", ""),) if value
        )
        # redact secrets
        input = _redact(input, secrets)
        actual_output = _redact(actual_output, secrets)
        if expected_output is not None:
            expected_output = _redact(expected_output, secrets)
        steps = tuple(_redact(step, secrets) for step in steps)

        started = time.monotonic()
        os.environ.update(_SDK_ENV)
        os.environ["DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE"] = str(config.timeout)
        for attempt in range(2):
            try:
                score, reason = _measure_once(config, input, actual_output, expected_output, steps)
            except EvaluationError:
                raise
            except ImportError:
                raise EvaluationProviderError(
                    "Evaluation SDK dependencies are unavailable"
                ) from None
            except (TimeoutError, AsyncTimeoutError):
                raise EvaluationTimeoutError(
                    "Response evaluation timed out"
                ) from None
            except (ValueError, TypeError, AttributeError):
                raise EvaluationResponseError(
                    "Judge returned an invalid response or SDK configuration"
                ) from None
            except Exception as error:
                status = _status_code(error)
                if attempt == 0 and status is not None and (status == 429 or status >= 500):
                    continue
                detail = f" (HTTP {status})" if status is not None else ""
                raise EvaluationProviderError(
                    f"Judge provider request failed{detail}"
                ) from None

            if (
                isinstance(score, bool)
                or not isinstance(score, (int, float))
                or not math.isfinite(score)
                or not 0 <= score <= 1
                or not isinstance(reason, str)
                or not reason.strip()
            ):
                raise EvaluationResponseError("Judge returned an invalid score or reason")

            return EvaluationResult(
                score=float(score),
                threshold=config.threshold,
                passed=score >= config.threshold,
                reason=_redact(reason, secrets),
                metric_name="Rancher AI Response",
                judge_model=_redact(config.model_name, secrets),
                rubric_version=version,
                elapsed_seconds=max(0.0, time.monotonic() - started),
            )
        raise AssertionError("Unreachable evaluation attempt state")
