"""Configuration, results and errors for the one-shot Rancher AI client.

Refer unit test in harvester_robot_tests/tests/unit/test_rancher_ai_config.py
"""

import math
import os
import re
from dataclasses import asdict, dataclass, field
from typing import Mapping, Optional, Union
from urllib.parse import urlsplit, urlunsplit


JSONValue = Union[None, bool, int, float, str, list["JSONValue"], dict[str, "JSONValue"]]
DEFAULT_ENDPOINT_PATH = (
    "/api/v1/namespaces/cattle-ai-agent-system/"
    "services/http:rancher-ai-agent:80/proxy/v1/ws/messages"
)


def _get_config_value(name: str, environ: Mapping[str, str], default=None) -> object:
    """Read a Robot scalar, falling back only when it is undefined or unavailable.
    """
    try:
        from robot.libraries.BuiltIn import BuiltIn, RobotNotRunningError
    except ModuleNotFoundError as error:
        if error.name != "robot":
            raise
    else:
        missing = object()
        try:
            value = BuiltIn().get_variable_value("${" + name + "}", missing)
        except RobotNotRunningError:
            pass
        else:
            if value is not missing:
                return value
    return environ.get(name, default)


@dataclass(frozen=True)
class StreamEvent:
    """A parsed control block, kept separately from the narrative."""

    tag: str
    data: JSONValue


@dataclass(frozen=True)
class ResourceReference:
    """An agent-reported resource identity, not independent cluster evidence."""

    name: str
    namespace: str
    cluster: str
    kind: str
    type: str


@dataclass(frozen=True)
class ConversationResult:
    """One response; completion does not mean the requested task succeeded."""

    prompt: str = field(repr=False)
    cluster_id: str
    answer: str = field(repr=False)
    chat_id: Optional[str]
    events: tuple[StreamEvent, ...]
    resources: tuple[ResourceReference, ...]
    transcript: str = field(repr=False)
    completed: bool
    elapsed_seconds: float

    def to_dict(self) -> dict:
        """Return an independent, JSON-serializable snapshot for reporting."""
        return asdict(self)


@dataclass(frozen=True)
class ConfirmationConversationResult:
    """Keep both responses; protocol completion is not proof of task success.
    """
    initial_response: ConversationResult = field(repr=False)
    final_response: ConversationResult = field(repr=False)
    decision: str
    elapsed_seconds: float

    @property
    def answer(self) -> str:
        """Return the final narrative without mixing it with the pending plan.
        """
        return self.final_response.answer

    @property
    def chat_id(self) -> Optional[str]:
        """Return the connection's conversation identifier, when supplied.
        """
        return self.final_response.chat_id or self.initial_response.chat_id

    @property
    def completed(self) -> bool:
        """Return whether both responses have complete message boundaries.
        """
        return self.initial_response.completed and self.final_response.completed

    def to_dict(self) -> dict:
        """Return an independent snapshot with fixed report field names.
        """
        return asdict(self)


class RancherAIError(Exception):
    """Base error with optional sanitized partial response evidence."""

    def __init__(self, message: str, *, partial_result: Optional[ConversationResult] = None):
        super().__init__(message)
        self.partial_result = partial_result


class RancherAIConfigError(RancherAIError):
    """Missing or invalid configuration/request, before a connection is made."""


class RancherAIConnectionError(RancherAIError):
    """Connection, handshake, TLS or transport failure."""


class RancherAIAuthenticationError(RancherAIConnectionError):
    """The endpoint rejected authentication or authorization (HTTP 401/403)."""


class RancherAITimeoutError(RancherAIError):
    """A socket operation or the overall conversation exceeded its deadline."""


class RancherAIProtocolError(RancherAIError):
    """Invalid tagged stream, JSON control block or text encoding."""


class RancherAIConfirmationError(RancherAIProtocolError):
    """The requested confirmation was missing, ambiguous or repeated."""


class RancherAIIncompleteResponseError(RancherAIProtocolError):
    """The stream ended without a complete, nonempty message."""


class RancherAIResponseTooLargeError(RancherAIProtocolError):
    """The configured response byte limit was exceeded."""


@dataclass
class RancherAIConfig:
    """Explicit config; Robot/environment lookup occurs only in ``from_env()``.
    """
    rancher_url: str                             # env["RANCHER_ENDPOINT"]
    api_token: str = field(repr=False)           # assign in client.py
    cluster_id: str                              # assign in client.py
    verify_tls: bool = True                      # env["RANCHER_AI_VERIFY_TLS"]
    ca_bundle: Optional[str] = None              # env["RANCHER_AI_CA_BUNDLE"]
    connect_timeout: float = 30.0                # env["RANCHER_AI_CONNECT_TIMEOUT"]
    timeout: float = 120.0                       # env["RANCHER_AI_TIMEOUT"]
    max_response_bytes: int = 2 * 1024 * 1024    # env["RANCHER_AI_MAX_RESPONSE_BYTES"]
    endpoint_path: str = DEFAULT_ENDPOINT_PATH

    @staticmethod
    def _is_valid_cookie_value(value: object) -> bool:
        """Check whether value contains only RFC 6265 cookie octets."""
        RFC6265_COOKIE_PATTERN = re.compile(r"[\x21\x23-\x2b\x2d-\x3a\x3c-\x5b\x5d-\x7e]*")
        return isinstance(value, str) and RFC6265_COOKIE_PATTERN.fullmatch(value) is not None

    def __post_init__(self) -> None:
        # Validate without exposing supplied values in exception messages.
        self.websocket_url

        if not isinstance(self.verify_tls, bool):
            raise RancherAIConfigError("RANCHER_AI_VERIFY_TLS must be a boolean")

        if self.ca_bundle is not None and (
            not isinstance(self.ca_bundle, str) or not self.ca_bundle.strip()
        ):
            raise RancherAIConfigError("RANCHER_AI_CA_BUNDLE must be a nonempty path")

        for name, value in (
            ("RANCHER_AI_CONNECT_TIMEOUT", self.connect_timeout),
            ("RANCHER_AI_TIMEOUT", self.timeout),
        ):
            if (isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(value)
                    or value <= 0):
                raise RancherAIConfigError(f"{name} must be a finite positive number")

        if (isinstance(self.max_response_bytes, bool)
                or not isinstance(self.max_response_bytes, int)
                or self.max_response_bytes <= 0):
            raise RancherAIConfigError("RANCHER_AI_MAX_RESPONSE_BYTES must be a positive integer")

    @property
    def websocket_url(self) -> str:
        """Convert only the scheme and preserve an optional Rancher base path."""
        try:
            if (not isinstance(self.rancher_url, str)
                    or any(c.isspace() or ord(c) < 0x20 or c == "\\" for c in self.rancher_url)):
                raise ValueError

            parsed = urlsplit(self.rancher_url)
            if (parsed.scheme not in ("http", "https")
                    or not parsed.hostname
                    or parsed.username is not None or parsed.password is not None
                    or "?" in self.rancher_url or "#" in self.rancher_url):
                raise ValueError

            parsed.port  # Validate malformed and out-of-range ports.
        except (ValueError, TypeError):
            raise RancherAIConfigError(
                "RANCHER_ENDPOINT must be an HTTP(S) URL without credentials, query or fragment"
            ) from None

        if (not isinstance(self.endpoint_path, str)
                or not self.endpoint_path.startswith("/")
                or self.endpoint_path.startswith("//")
                or any(c.isspace() or ord(c) < 0x20 or c in "?#\\" for c in self.endpoint_path)):
            raise RancherAIConfigError("endpoint_path must be an absolute URL path")

        return urlunsplit((
            "wss" if parsed.scheme == "https" else "ws",
            parsed.netloc,
            parsed.path.rstrip("/") + self.endpoint_path,
            "", "",
        ))

    @classmethod
    def from_env(cls, environ: Optional[Mapping[str, str]] = None) -> "RancherAIConfig":
        """Read AI settings from Robot first, then the supplied environment and defaults.
        """
        env = os.environ if environ is None else environ

        tls = _get_config_value("RANCHER_AI_VERIFY_TLS", env, "true")
        if isinstance(tls, str):
            tls = tls.strip().lower()
            if tls in ("true", "false", "1", "0", "yes", "no"):
                tls = tls in ("true", "1", "yes")
        if not isinstance(tls, bool):
            raise RancherAIConfigError("RANCHER_AI_VERIFY_TLS must be true or false")

        numbers = {}
        for name, default, converter in (
            ("RANCHER_AI_CONNECT_TIMEOUT", "30", float),
            ("RANCHER_AI_TIMEOUT", "120", float),
            ("RANCHER_AI_MAX_RESPONSE_BYTES", "2097152", int),
        ):
            value = _get_config_value(name, env, default)
            try:
                if (isinstance(value, bool)
                        or not isinstance(value, (str, int, float))
                        or (converter is int and isinstance(value, float))):
                    raise ValueError
                numbers[name] = converter(value)
            except (ValueError, TypeError, OverflowError):
                raise RancherAIConfigError(f"{name} has an invalid numeric value") from None

        ca_bundle = _get_config_value("RANCHER_AI_CA_BUNDLE", env)
        if ca_bundle == "":
            ca_bundle = None
        if ca_bundle is not None and not isinstance(ca_bundle, str):
            raise RancherAIConfigError("RANCHER_AI_CA_BUNDLE must be a nonempty path")

        return cls(
            rancher_url=env["RANCHER_ENDPOINT"],
            api_token="",
            cluster_id="",
            verify_tls=tls,
            ca_bundle=ca_bundle,
            connect_timeout=numbers["RANCHER_AI_CONNECT_TIMEOUT"],
            timeout=numbers["RANCHER_AI_TIMEOUT"],
            max_response_bytes=numbers["RANCHER_AI_MAX_RESPONSE_BYTES"],
        )
