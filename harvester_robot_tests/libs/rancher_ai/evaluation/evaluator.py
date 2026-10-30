"""Generic synchronous DeepEval evaluation, independent of the AI client.
"""

import math
import os
import re
import time
from asyncio import TimeoutError as AsyncTimeoutError
from contextlib import ExitStack, suppress
from typing import Optional
from utility.utility import logging

from ..models import _get_config_value
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


def _close(client) -> None:
    """Release an owned SDK client without hiding an evaluation failure.
    """
    with suppress(Exception):
        client.close()


def _create_gemini_model(config: EvaluationConfig, resources: ExitStack):
    """Create Gemini and register its clients with the caller's resource stack.
    """
    import httpx
    from deepeval.models import GeminiModel
    from google.genai.types import HttpOptions, HttpRetryOptions

    # Gemini creates further clients during generation. Their shared
    # caller-owned HTTP transport has one explicit lifecycle.
    transport = httpx.Client()
    resources.callback(_close, transport)
    model = GeminiModel(
        model=config.model_name, api_key=config.api_key,
        temperature=0, use_vertexai=False, vertexai=False,
        generation_kwargs={"automatic_function_calling": {"disable": True}},
        http_options=HttpOptions(
            timeout=max(1, math.ceil(config.timeout * 1000)),
            retry_options=HttpRetryOptions(attempts=1),
            httpx_client=transport,
        ),
    )
    resources.callback(_close, model.model)
    return model


def _create_ollama_model(config: EvaluationConfig, resources: ExitStack):
    """Reuse one sync client, including calls made by the SDK constructor.
    """
    from deepeval.models import OllamaModel

    client = None

    class SyncOllamaModel(OllamaModel):
        """Keep stock generation/schema handling with an owned sync client.
        """
        def load_model(self, async_mode: bool = False):
            """Register ownership as soon as a client exists, even during init.
            """
            nonlocal client
            if async_mode:
                raise EvaluationConfigError("Response evaluation supports synchronous Ollama only")
            if client is None:
                client = super().load_model(async_mode=False)
                resources.callback(_close, client)
            return client

    return SyncOllamaModel(
        model=config.model_name, base_url=config.base_url,
        temperature=0, timeout=config.timeout, follow_redirects=False,
    )


def _measure_once(
    config: EvaluationConfig,
    input: str,
    actual_output: str,
    expected_output: Optional[str],
    evaluation_steps: tuple[str, ...]
) -> tuple[object, object]:
    """Measure output by LLM-as-a-judge with ordinary SDK calls; no worker or generated criteria.

    Returns:
        (score, reason): score is a float in [0, 1], reason is a nonempty string.
    Raises:
        EvaluationError on any failure
    """
    import httpx
    from deepeval.metrics import GEval
    from deepeval.test_case import LLMTestCase, SingleTurnParams
    from tenacity import RetryError

    with ExitStack() as resources:
        try:
            if config.provider == "ollama":
                model = _create_ollama_model(config, resources)
                logging(f"Using Ollama model {config.model_name}")
            elif config.provider == "gemini":
                model = _create_gemini_model(config, resources)
                logging(f"Using Gemini model {config.model_name}")
            else:
                raise EvaluationConfigError("Evaluation provider must be gemini or ollama")
        except EvaluationError:
            raise
        except ImportError:
            raise EvaluationProviderError("Evaluation SDK dependencies are unavailable") from None
        except Exception as error:
            status = _status_code(error)
            detail = f" (HTTP {status})" if status is not None else ""
            raise EvaluationProviderError(
                f"Could not initialize {config.provider} judge{detail}"
            ) from None

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
        try:
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
        evaluation_steps: Optional[list[str]] = None,
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
                not isinstance(evaluation_steps, list)
                or isinstance(evaluation_steps, (str, bytes))
                or not evaluation_steps
            ):
                raise EvaluationConfigError(
                    "evaluation_steps must be a nonempty list of strings"
                )
            for step in evaluation_steps:
                _validate_text(step, "evaluation_steps item")
            steps = tuple(evaluation_steps)
            version = "custom-v1"

        config = self.config if self.config is not None else EvaluationConfig.from_env()
        secrets = tuple(
            value for value in (
                config.api_key,
                _get_config_value("GEMINI_API_KEY", os.environ, ""),
                os.environ.get("GEMINI_API_KEY", ""),
                os.environ.get("OLLAMA_API_KEY", "")
            ) if isinstance(value, str) and value
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
                    f"Judge provider request failed{detail}: {_redact(str(error), secrets)}"
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
