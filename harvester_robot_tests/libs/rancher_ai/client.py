"""One-shot WebSocket conversations with Rancher AI, without Robot dependencies.

Refer unit test in harvester_robot_tests/tests/unit/test_rancher_ai_client.py
"""

import errno
import json
import os
import re
import requests
import socket
import ssl
import time
import warnings
from contextlib import suppress
from dataclasses import asdict
from typing import Callable, Optional, cast, overload
import logging
import websocket

from .models import (
    JSONValue,
    RancherAIConfig,
    ConfirmationConversationResult, RancherAIConfirmationError,
    ConversationResult, ResourceReference, StreamEvent,
    RancherAIError,
    RancherAIConfigError,
    RancherAIConnectionError, RancherAIAuthenticationError,
    RancherAIProtocolError, RancherAIIncompleteResponseError,
    RancherAIResponseTooLargeError, RancherAITimeoutError
)
from .protocol import RancherAIConfirmationStreamParser, RancherAIStreamParser

logger = logging.getLogger(__name__)


@overload
def _redact(value: str, token: str) -> str: ...


@overload
def _redact(value: JSONValue, token: str) -> JSONValue: ...


def _redact(value: JSONValue, token: str) -> JSONValue:
    """Mask raw and JSON-escaped tokens in text and free-form JSON keys and values.
    """
    if isinstance(value, str):
        characters = []
        for char in token:
            alternatives = [re.escape(char), rf"(?i:\\u{ord(char):04x})"]
            if char == "/":
                alternatives.append(r"\\/")
            characters.append("(?:" + "|".join(alternatives) + ")")
        return re.sub("".join(characters), "[REDACTED]", value)
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


class ConfirmationWebSocket(websocket.WebSocket):
    """Check deadlines per socket read and payload lengths before frame allocation.

    The installed websocket-client frame reader otherwise assembles a complete
    fragmented message before returning to the application-level byte/deadline checks.
    This socket is privately owned by one confirmation conversation.
    """
    def __init__(self, remaining: Callable[[], float], max_response_bytes: int, **kwargs):
        self._remaining = remaining
        self._bytes_left = max_response_bytes
        super().__init__(**kwargs)

    def _recv(self, bufsize: int) -> bytes:
        """Prevent a stream of small socket reads from resetting the deadline.
        """
        self.settimeout(self._remaining())
        data = super()._recv(bufsize)
        self._remaining()
        return data

    def recv_frame(self):
        """Inspect announced lengths before the dependency reads or joins payloads.
        """
        self._remaining()
        buffer = self.frame_buffer
        with buffer.lock:
            if buffer.needs_header():
                buffer.recv_header()
            if buffer.header is None:
                raise RancherAIProtocolError("Missing WebSocket frame header")
            if buffer.needs_length():
                buffer.recv_length()
            length = buffer.length
            if length is None:
                raise RancherAIProtocolError("Missing WebSocket frame length")
            opcode = buffer.header[4]
            if opcode in (websocket.ABNF.OPCODE_TEXT, websocket.ABNF.OPCODE_CONT):
                if length > self._bytes_left:
                    raise RancherAIResponseTooLargeError(
                        "Rancher AI response exceeded the byte limit",
                    )
                self._bytes_left -= length
            elif opcode in (websocket.ABNF.OPCODE_PING, websocket.ABNF.OPCODE_PONG,
                            websocket.ABNF.OPCODE_CLOSE):
                if length > 125:
                    raise RancherAIProtocolError("Oversized WebSocket control frame")
            else:
                raise RancherAIProtocolError("Expected a WebSocket text message")
        # The header/length stay cached. Release its lock before the normal reader
        # acquires it again for masks, payload, frame reset and protocol validation.
        return super().recv_frame()


class RancherAIClient:
    """Client for submitting user requests to the Rancher AI agent."""

    def __init__(self, config: Optional[RancherAIConfig] = None):
        # Import/instantiation can be used by unrelated suites without AI credentials.
        self.config = config
        try:
            from robot.libraries.BuiltIn import BuiltIn
            self.rancher_endpoint = BuiltIn().get_variable_value("${RANCHER_ENDPOINT}")
            self.rancher_username = BuiltIn().get_variable_value("${RANCHER_USERNAME}")
            self.rancher_password = BuiltIn().get_variable_value("${RANCHER_PASSWORD}")
        except Exception:
            self.rancher_endpoint = os.getenv("RANCHER_ENDPOINT")
            self.rancher_username = os.getenv("RANCHER_USERNAME")
            self.rancher_password = os.getenv("RANCHER_PASSWORD")
        self.rancher_token = None
        self.rancher_session = None
        self._authenticate_rancher()

    def prompt(self, prompt: str, harvester_cluster_id: str) -> ConversationResult:
        """One-shot Conversation: Submit a user request and wait for a complete response.

        * Opens a fresh chat, sends once, receives once and closes.
        * Does not reconnects or replays a mutation after a failure.
        * Does not approve confirmation, evaluate task success, or verify cluster resources.

        Args:
            prompt: The user-facing request, which is an instruction or a task description.
            harvester_cluster_id: Harvester cluster ID to be used in the Rancher AI context.

        Returns:
            A ConversationResult object, returned as-is even if the task fails or the response
            asks for confirmation.
        """
        config = self.config if self.config is not None else RancherAIConfig.from_env()
        config.api_token = self.rancher_token
        config.cluster_id = harvester_cluster_id
        if not isinstance(prompt, str) or not prompt.strip():
            raise RancherAIConfigError("prompt must be a nonempty string")

        try:
            request_context = {"cluster": harvester_cluster_id}
            payload = json.dumps({
                "prompt": prompt,
                "agent": "virtualization",
                "context": request_context
                },
                allow_nan=False
            )
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
                cluster_id=_redact(harvester_cluster_id, token),
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

    def prompt_and_confirm(
        self, prompt: str, harvester_cluster_id: str, decision: str = "yes",
    ) -> ConfirmationConversationResult:
        """Confirmation Conversation: Send one yes/no decision after a confirmation request.

        Uses one socket for both turns and preserves their separate responses.
        Failures retain the active partial_result and sanitized conversation_history.

        Args:
            prompt: Original user request.
            harvester_cluster_id: Target Harvester cluster ID.
            decision: Explicit yes (confirm) or no (cancel).

        Returns:
            Both responses, with answer referring to the final narrative.

        Raises:
            RancherAIConfirmationError: Missing, ambiguous or repeated confirmation request.
        """
        if not isinstance(prompt, str) or not prompt.strip():
            raise RancherAIConfigError("prompt must be a nonempty string")
        if not isinstance(harvester_cluster_id, str) or not harvester_cluster_id.strip():
            raise RancherAIConfigError("harvester_cluster_id must be a nonempty string")
        if not isinstance(decision, str) or decision.strip().lower() not in ("yes", "no"):
            raise RancherAIConfigError("decision must be yes or no")
        decision = decision.strip().lower()
        token = self.rancher_token
        if (not isinstance(token, str) or not token
                or not RancherAIConfig._is_valid_cookie_value(token)):
            raise RancherAIConfigError("A valid authenticated Rancher token is required")

        config = self.config if self.config is not None else RancherAIConfig.from_env()
        # Snapshot settings; never mutate the caller's config or use mutable auth state mid-call.
        websocket_url = config.websocket_url
        connect_timeout, timeout = config.connect_timeout, config.timeout
        max_bytes = config.max_response_bytes
        ssl_options: dict = {
            "cert_reqs": ssl.CERT_REQUIRED if config.verify_tls else ssl.CERT_NONE,
            "check_hostname": config.verify_tls,
        }
        if config.ca_bundle:
            ssl_options["ca_certs"] = config.ca_bundle
        if not config.verify_tls:
            warnings.warn("TLS verification is disabled for Rancher AI", RuntimeWarning,
                          stacklevel=2)

        payload = json.dumps({
            "prompt": prompt,
            "agent": "virtualization",
            "context": {"cluster": harvester_cluster_id},
        }, allow_nan=False)
        confirmation_payload = json.dumps({
            "prompt": decision,
            "agent": "virtualization",
            "context": {},
            "tags": ["confirmation"],
        }, allow_nan=False)
        started = time.monotonic()
        deadline = started + timeout
        turn_started = started
        parser = RancherAIConfirmationStreamParser(max_bytes)
        initial_response: Optional[ConversationResult] = None
        active_prompt = prompt
        stage = "connect"

        def remaining() -> float:
            """Keep control frames and both turns within one absolute deadline.
            """
            value = deadline - time.monotonic()
            if value <= 0:
                raise RancherAITimeoutError("Rancher AI conversation deadline exceeded")
            return value

        def result() -> ConversationResult:
            """Sanitize free-form content while preserving fixed result schema keys.
            """
            return ConversationResult(
                prompt=_redact(active_prompt, token),
                cluster_id=_redact(harvester_cluster_id, token),
                answer=_redact(parser.answer, token),
                chat_id=_redact(parser.chat_id, token) if parser.chat_id else None,
                events=tuple(StreamEvent(event.tag, _redact(event.data, token))
                             for event in parser.events),
                resources=tuple(ResourceReference(**{
                    key: _redact(value, token) for key, value in asdict(item).items()
                }) for item in parser.resources),
                transcript=_redact(parser.transcript, token),
                completed=parser.completed,
                elapsed_seconds=max(0.0, time.monotonic() - turn_started),
            )

        def attach_history(error: RancherAIError) -> None:
            """Attach both-turn evidence without changing existing error constructors.
            """
            partial = result()
            error.partial_result = partial
            history = (partial,) if initial_response is None else (initial_response, partial)
            error.conversation_history = history

        connection = ConfirmationWebSocket(
            remaining, max_bytes, sslopt=ssl_options, enable_multithread=True,
        )

        def receive_turn() -> None:
            """Receive a full framed turn; neither a close nor an idle timeout completes it.
            """
            while not parser.completed:
                connection.settimeout(remaining())
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

        try:
            try:
                connection.connect(
                    websocket_url, cookie=f"R_SESS={token}",
                    timeout=min(connect_timeout, remaining()), redirect_limit=0,
                )
                status = connection.getstatus()
                if status != 101:
                    error_class = (RancherAIAuthenticationError if status in (401, 403)
                                   else RancherAIConnectionError)
                    raise error_class(
                        f"Rancher AI handshake rejected (HTTP {status}); expected 101",
                    )
                stage = "send_initial"
                connection.settimeout(remaining())
                connection.send(payload)

                stage = "receive_initial"
                receive_turn()
                print(f"Prompt: {prompt}")
                print(f"Answer: {parser.answer}")
                if not parser.requires_confirmation:
                    raise RancherAIConfirmationError("Response did not request confirmation")

                initial_response = result()
                bytes_left = max_bytes - parser.received_bytes
                # Switch before any second-turn failure so history does not duplicate the plan.
                previous_chat_id = parser.chat_id
                active_prompt = decision
                turn_started = time.monotonic()
                parser = RancherAIConfirmationStreamParser(max(1, bytes_left), previous_chat_id)
                if bytes_left <= 0:
                    raise RancherAIResponseTooLargeError(
                        "No response byte budget left for confirmation",
                    )

                stage = "send_confirmation"
                connection.settimeout(remaining())
                connection.send(confirmation_payload)

                stage = "receive_confirmation"
                receive_turn()
                if parser.requires_confirmation:
                    raise RancherAIConfirmationError(
                        "A second confirmation request is not allowed",
                    )
                return ConfirmationConversationResult(
                    initial_response=initial_response, final_response=result(), decision=decision,
                    elapsed_seconds=max(0.0, time.monotonic() - started),
                )
            except (websocket.WebSocketTimeoutException, TimeoutError):
                raise RancherAITimeoutError("Rancher AI socket operation timed out") from None
            except websocket.WebSocketBadStatusException as error:
                error_class = (RancherAIAuthenticationError if error.status_code in (401, 403)
                               else RancherAIConnectionError)
                raise error_class(
                    f"Rancher AI handshake rejected (HTTP {error.status_code})",
                ) from None
            except websocket.WebSocketConnectionClosedException:
                raise RancherAIIncompleteResponseError(
                    "WebSocket closed before </message>",
                ) from None
            except (websocket.WebSocketException, OSError) as error:
                reason = _transport_reason(error)
                raise RancherAIConnectionError(
                    f"Rancher AI WebSocket transport failed during {stage}: {reason}",
                ) from None
        except RancherAIError as error:
            attach_history(error)
            raise
        finally:
            # Suppress cleanup errors thus not overwrite the primary failure
            with suppress(Exception):
                connection.close(timeout=0)
            with suppress(Exception):
                connection.shutdown()

    def _authenticate_rancher(self):
        """Authenticate with Rancher and get token"""
        if self.rancher_token and self.rancher_session:
            return  # Already authenticated

        session = requests.Session()
        session.verify = False
        session.headers.update({"Content-Type": "application/json"})

        from urllib.parse import urljoin
        url = urljoin(self.rancher_endpoint, "v3-public/localProviders/local?action=login")
        response = session.post(url, json={
            "username": self.rancher_username,
            "password": self.rancher_password
        })
        if response.status_code != 201:
            logger.info(f"Auth failed - Status: {response.status_code}, Response: {response.text}")
            raise Exception(
                f"Failed to authenticate with Rancher: "
                f"{response.status_code} {response.text}"
            )

        token = response.json().get("token")
        if not token:
            raise Exception("No token in authentication response")

        self.rancher_token = token
        self.rancher_session = session
        session.headers.update({"Authorization": f"Bearer {token}"})
