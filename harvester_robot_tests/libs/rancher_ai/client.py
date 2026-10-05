"""One-shot WebSocket conversations with Rancher AI, without Robot dependencies.

Refer unit test in harvester_robot_tests/tests/unit/test_rancher_ai_client.py
"""

import errno
import json
import socket
import ssl
import time
import warnings
from contextlib import suppress
from dataclasses import asdict
from typing import Mapping, Optional, cast, overload

import websocket

from .models import (
    JSONValue,
    RancherAIConfig,
    ConversationResult, ResourceReference, StreamEvent,
    RancherAIError,
    RancherAIConfigError,
    RancherAIConnectionError, RancherAIAuthenticationError,
    RancherAIProtocolError, RancherAIIncompleteResponseError,
    RancherAITimeoutError
)
from .protocol import RancherAIStreamParser


@overload
def _redact(value: str, token: str) -> str: ...


@overload
def _redact(value: JSONValue, token: str) -> JSONValue: ...


def _redact(value: JSONValue, token: str) -> JSONValue:
    """Hiding sensitive information."""
    if isinstance(value, str):
        return value.replace(token, "[REDACTED]")
    if isinstance(value, list):
        return [_redact(item, token) for item in value]
    if isinstance(value, dict):
        return {_redact(key, token): _redact(item, token)
                for key, item in value.items()}
    return value


def _transport_reason(error: Exception) -> str:
    """Classify failures using fixed text, never upstream bodies/headers/filenames."""
    if isinstance(error, ssl.SSLCertVerificationError):
        reasons = {
            9: "certificate is not yet valid",
            10: "certificate has expired",
            18: "self-signed certificate",
            19: "self-signed certificate chain",
            20: "issuer is not trusted",
            21: "certificate chain cannot be verified",
            62: "hostname mismatch",
            64: "IP address mismatch",
        }
        code = getattr(error, "verify_code", None)
        detail = reasons.get(code, "") if isinstance(code, int) else ""
        reason = "TLS certificate verification failed"
        if detail:
            reason += f" ({detail})"
        return reason + "; check certificate trust, validity and hostname"
    if isinstance(error, ssl.SSLError):
        return "TLS handshake or record failed"
    if isinstance(error, (socket.gaierror, websocket.WebSocketAddressException)):
        return "DNS resolution failed (Rancher or proxy hostname)"
    if isinstance(error, ConnectionRefusedError):
        return "TCP connection refused"
    if isinstance(error, ConnectionResetError):
        return "connection reset by peer"
    if isinstance(error, FileNotFoundError):
        return "required local file is missing; check RANCHER_AI_CA_BUNDLE"
    if isinstance(error, PermissionError):
        return "permission denied; check network and CA file permissions"
    if isinstance(error, websocket.WebSocketProxyException):
        return "proxy connection failed; check proxy settings"
    if isinstance(error, websocket.WebSocketProtocolException):
        return "invalid WebSocket handshake or frame"
    if isinstance(error, OSError) and error.errno in (errno.ENETUNREACH, errno.EHOSTUNREACH):
        return "network or host is unreachable"
    return "unspecified transport error"


class RancherAIClient:
    """Client for submitting user requests to the Rancher AI agent."""

    def __init__(self, config: Optional[RancherAIConfig] = None):
        # Import/instantiation can be used by unrelated suites without AI credentials.
        self.config = config

    def ask(self,
            prompt: str,
            context: Optional[Mapping[str, JSONValue]] = None
            ) -> ConversationResult:
        """Submit a user request and wait for a complete response.

        * Opens a fresh chat, sends once, receives once and closes.
        * Does not reconnects or replays a mutation after a failure.
        * Does not approve confirmation, evaluate task success, or verify cluster resources.

        Args:
            prompt: The user-facing request, which is an instruction or a task description.
            context: The context information. For example, use {"cluster": RANCHER_CLUSTER_ID}
                when operating on a specific Harvester cluster.

        Returns:
            A ConversationResult object, returned as-is even if the task fails or the response
            asks for confirmation.
        """
        config = self.config if self.config is not None else RancherAIConfig.from_env()
        if not isinstance(prompt, str) or not prompt.strip():
            raise RancherAIConfigError("prompt must be a nonempty string")
        if context is not None and not isinstance(context, Mapping):
            raise RancherAIConfigError("context must be a JSON-serializable mapping")

        request_context: dict[str, JSONValue] = {"cluster": config.cluster_id}
        if context is not None:
            request_context.update(context)

        cluster = request_context["cluster"]
        if not isinstance(cluster, str) or not cluster or any(
            char.isspace() or ord(char) < 0x20 for char in cluster
        ):
            raise RancherAIConfigError("context.cluster must be nonempty without whitespace")

        try:
            payload = json.dumps({"prompt": prompt, "context": request_context}, allow_nan=False)
        except (ValueError, TypeError, RecursionError):
            raise RancherAIConfigError("prompt and context must be valid JSON data") from None
        parser = RancherAIStreamParser(config.max_response_bytes)
        started = time.monotonic()
        deadline = started + config.timeout

        def remaining() -> float:
            value = deadline - time.monotonic()
            if value <= 0:
                raise RancherAITimeoutError("Rancher AI conversation deadline exceeded")
            return value

        def result() -> ConversationResult:
            # Redact after concatenation, including tokens echoed across chunk boundaries.
            token = config.api_token
            return ConversationResult(
                prompt=_redact(prompt, token),
                cluster_id=_redact(cluster, token),
                answer=_redact(parser.answer, token),
                chat_id=_redact(parser.chat_id, token) if parser.chat_id else None,
                events=tuple(StreamEvent(event.tag, _redact(event.data, token))
                             for event in parser.events),
                resources=tuple(ResourceReference(**cast(dict, _redact(asdict(item), token)))
                                for item in parser.resources),
                transcript=_redact(parser.transcript, token),
                completed=parser.completed, elapsed_seconds=max(0.0, time.monotonic() - started),
            )

        ssl_options: dict = {
            "cert_reqs": ssl.CERT_REQUIRED if config.verify_tls else ssl.CERT_NONE,
            "check_hostname": config.verify_tls,
        }
        if config.ca_bundle:
            ssl_options["ca_certs"] = config.ca_bundle
        if not config.verify_tls:
            warnings.warn("TLS verification is disabled for Rancher AI", RuntimeWarning,
                          stacklevel=2)

        # Own the socket before connect so a failed handshake also gets cleaned up.
        connection = websocket.WebSocket(sslopt=ssl_options, enable_multithread=True)
        stage = "connect"
        try:
            connection.connect(
                config.websocket_url, cookie=f"R_SESS={config.api_token}",
                timeout=min(config.connect_timeout, remaining()), redirect_limit=0,
            )
            # websocket-client with redirect_limit=0 can return a non-101 handshake.
            # Refuse it rather than follow a Location with the authentication cookie.
            status = connection.getstatus()
            if status != 101:
                error_class = (RancherAIAuthenticationError if status in (401, 403)
                               else RancherAIConnectionError)
                raise error_class(f"Rancher AI handshake rejected (HTTP {status}); expected 101")
            stage = "send"
            connection.settimeout(remaining())
            connection.send(payload)
            stage = "receive"
            while not parser.completed:
                connection.settimeout(remaining())
                # Surface control frames so continuous ping/pong traffic cannot reset our deadline.
                opcode, raw = connection.recv_data(control_frame=True)
                remaining()
                if opcode == websocket.ABNF.OPCODE_CLOSE:
                    parser.finish()
                elif opcode in (websocket.ABNF.OPCODE_PING, websocket.ABNF.OPCODE_PONG):
                    continue
                elif opcode != websocket.ABNF.OPCODE_TEXT:
                    raise RancherAIProtocolError("Expected a WebSocket text message")
                elif not raw:
                    raise RancherAIIncompleteResponseError("Connection returned an empty response")
                else:
                    try:
                        text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
                    except UnicodeError:
                        raise RancherAIProtocolError("Invalid UTF-8 response text") from None
                    parser.feed(text)
            return result()
        except RancherAIError as error:
            error.partial_result = result()
            raise
        except (websocket.WebSocketTimeoutException, TimeoutError):
            raise RancherAITimeoutError(
                "Rancher AI socket operation timed out", partial_result=result(),
            ) from None
        except websocket.WebSocketBadStatusException as error:
            error_class = (RancherAIAuthenticationError if error.status_code in (401, 403)
                           else RancherAIConnectionError)
            raise error_class(f"Rancher AI handshake rejected (HTTP {error.status_code})",
                              partial_result=result()) from None
        except websocket.WebSocketConnectionClosedException:
            raise RancherAIIncompleteResponseError(
                "WebSocket closed before </message>", partial_result=result(),
            ) from None
        except (websocket.WebSocketException, OSError) as error:
            # Upstream messages can contain request headers or remote bodies; do not forward them.
            reason = _transport_reason(error)
            raise RancherAIConnectionError(
                f"Rancher AI WebSocket transport failed during {stage}: {reason}",
                partial_result=result(),
            ) from None
        finally:
            # Cleanup errors must not hide the response or the primary failure.
            with suppress(Exception):
                connection.close(timeout=0)  # No close-handshake wait beyond the deadline.
            with suppress(Exception):
                connection.shutdown()
