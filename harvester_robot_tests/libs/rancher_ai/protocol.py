"""Incremental parser for Rancher AI's tagged text stream (not XML or JSON frames).

Refer unit test in harvester_robot_tests/tests/unit/test_rancher_ai_protocol.py
"""

import json
import math
from typing import Optional, cast

from .models import (
    JSONValue, RancherAIConfirmationError, RancherAIIncompleteResponseError,
    RancherAIProtocolError, RancherAIResponseTooLargeError, ResourceReference, StreamEvent,
)


KNOWN_TAGS = (
    # message boundary: carring narrative text and control blocks.
    "message",
    # control blocks: in message block, carrying JSON data
    "chat-metadata",
    "processing-subagent-start",
    "processing-subagent-end",
    "mcp-response",
)
MARKERS = tuple(marker for tag in KNOWN_TAGS for marker in (f"<{tag}>", f"</{tag}>"))

_CONFIRMATION_TAG = "confirmation-response"
_CONFIRMATION_MARKERS = tuple(
    marker
    for tag in (*KNOWN_TAGS, _CONFIRMATION_TAG)
    for marker in (f"<{tag}>", f"</{tag}>")
)


def _unique_object(pairs: list[tuple[str, JSONValue]]) -> dict[str, JSONValue]:
    """Reject ambiguous control objects rather than silently choosing the last key.
    """
    result: dict[str, JSONValue] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate control key")
        result[key] = value
    return result


def _finite_float(value: str) -> float:
    """Reject numeric overflow before storing structured response evidence.
    """
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("Non-finite control number")
    return number


def _reject_constant(value: str) -> None:
    raise ValueError("Nonstandard JSON constant")


class RancherAIStreamParser:
    """Feed text chunks, preserving narrative text and separating known control tags."""

    def __init__(self, max_response_bytes: int = 2 * 1024 * 1024):
        if (isinstance(max_response_bytes, bool) or not isinstance(max_response_bytes, int)
                or max_response_bytes <= 0):
            raise ValueError("max_response_bytes must be a positive integer")
        self.max_response_bytes = max_response_bytes
        self.completed = False
        self.chat_id = None
        self.events: list[StreamEvent] = []
        self.resources: list[ResourceReference] = []
        self._frames: list[str] = []
        self._answer: list[str] = []
        self._pending = ""
        self._started = False
        self._control_tag = None
        self._scan_position = 0
        self._in_string = False
        self._escaped = False
        self._received_bytes = 0

    @property
    def answer(self) -> str:
        return "".join(self._answer)

    @property
    def transcript(self) -> str:
        return "".join(self._frames)

    def feed(self, chunk: str) -> None:
        """Consume arbitrary chunk boundaries; stop at the first complete message."""
        if self.completed:
            raise RancherAIProtocolError("This one-shot message is already complete")

        if not isinstance(chunk, str):
            raise RancherAIProtocolError("Expected a WebSocket text message")
        try:
            size = len(chunk.encode("utf-8"))
        except UnicodeError:
            raise RancherAIProtocolError("Invalid UTF-8 response text") from None
        if self._received_bytes + size > self.max_response_bytes:
            raise RancherAIResponseTooLargeError("Rancher AI response exceeded the byte limit")

        self._received_bytes += size
        self._frames.append(chunk)
        self._pending += chunk
        while self._pending and not self.completed:
            if self._control_tag is not None:
                if not self._consume_control():
                    break
            elif not self._consume_text():
                break

    def finish(self) -> None:
        """Require the actual closing marker, not connection closure or an idle timeout."""
        if not self.completed:
            raise RancherAIIncompleteResponseError("Response ended before a complete </message>")

    def _append_text(self, text: str) -> None:
        if self._started:
            self._answer.append(text)
        elif text.strip():
            raise RancherAIProtocolError("Unexpected text before <message>")

    def _consume_text(self) -> bool:
        """Consume narrative text until an opening bracket is found, or the chunk ends.
        """
        position = self._pending.find("<")
        # Consume text until an opening bracket is found
        if position == -1:
            # not found
            self._append_text(self._pending)
            self._pending = ""
            return True
        if position:
            # found but not at the start
            self._append_text(self._pending[:position])
            self._pending = self._pending[position:]
            return True

        # Handle tags
        # - known
        for marker in MARKERS:
            if not self._pending.startswith(marker):
                continue

            self._pending = self._pending[len(marker):]
            if marker == "<message>":
                if self._started:
                    raise RancherAIProtocolError("Duplicate <message> marker")
                self._started = True
            elif marker == "</message>":
                if not self._started:
                    raise RancherAIProtocolError("Closing marker without <message>")
                if not self.answer.strip():
                    raise RancherAIIncompleteResponseError("Completed message without answer text")
                self.completed = True
            elif marker.startswith("</"):
                # control blocks without opening, see _consume_control() for the other cases
                raise RancherAIProtocolError("Unmatched control closing marker")
            else:
                # control blocks' opening marker
                self._control_tag = marker[1:-1]
                self._scan_position = 0
                self._in_string = False
                self._escaped = False
            return True

        # - unknown
        if any(marker.startswith(self._pending) for marker in MARKERS):
            # A registered marker is split across chunks (e.g. "<mes"), wait for the next chunk.
            return False
        # regarding unknown tags as narrative text
        self._append_text("<")
        self._pending = self._pending[1:]
        return True

    def _consume_control(self) -> bool:
        """Scan each character once; tag-like text inside JSON strings is not framing."""
        # The opening marker was consumed by _consume_text(); find its matching closing marker.
        closing = f"</{self._control_tag}>"
        # Resume from the saved position when feed() appends another chunk.
        while self._scan_position < len(self._pending):
            position = self._scan_position
            char = self._pending[position]

            # Inside a JSON string, quotes and tag-like text are data rather than framing.
            if self._in_string:
                if self._escaped:
                    self._escaped = False
                elif char == "\\":
                    self._escaped = True
                elif char == '"':
                    # An unescaped quote after a string ends a JSON string.
                    self._in_string = False
            elif char == '"':
                # An unescaped quote outside a string starts a JSON string.
                self._in_string = True
            elif char == "<":
                # Outside JSON strings, a complete matching marker ends the control block.
                if self._pending.startswith(closing, position):
                    self._record_control(self._pending[:position])
                    self._pending = self._pending[position + len(closing):]
                    self._control_tag = None
                    return True

                # A matching closing marker may be split across chunks; wait at this position.
                if closing.startswith(self._pending[position:]):
                    return False

                if self._pending.startswith("</message>", position):
                    raise RancherAIProtocolError("Unclosed control block before </message>")

            # If not return yet, preserve scanning state so not rescanning processed characters.
            self._scan_position += 1

        # No complete closing marker yet; retain the buffered JSON and wait for more input.
        return False

    def _record_control(self, raw: str) -> None:
        try:
            data = cast(JSONValue, json.loads(raw, parse_constant=_reject_constant))
        except (ValueError, RecursionError):
            raise RancherAIProtocolError("Invalid JSON in Rancher AI control block") from None

        # recursively visits the downstream redaction/serialization data.
        pending = [(data, 0)]
        while pending:
            value, depth = pending.pop()
            if depth > 64:
                raise RancherAIProtocolError("Control JSON exceeds the nesting limit (64)")
            if isinstance(value, dict):
                pending.extend((item, depth + 1) for item in value.values())
            elif isinstance(value, list):
                pending.extend((item, depth + 1) for item in value)

        tag = cast(str, self._control_tag)
        if tag == "chat-metadata":
            if not isinstance(data, dict) or (
                "chatId" in data and not isinstance(data["chatId"], str)
            ):
                raise RancherAIProtocolError("Invalid chat metadata")
            self.chat_id = cast(str, data["chatId"]) if "chatId" in data else None
        if tag == "mcp-response":
            items = data if isinstance(data, list) else [data]
            keys = ("name", "namespace", "cluster", "kind", "type")
            for item in items:
                if isinstance(item, dict) and all(
                    isinstance(item.get(key), str) and item[key] for key in keys
                ):
                    self.resources.append(ResourceReference(
                        **{key: cast(str, item[key]) for key in keys}
                    ))
        self.events.append(StreamEvent(tag, data))


class RancherAIConfirmationStreamParser(RancherAIStreamParser):
    """Parse one confirmation-aware turn, reusing JSON scanning and byte limits.
    """
    def __init__(
        self, max_response_bytes: int = 2 * 1024 * 1024, chat_id: Optional[str] = None,
    ):
        super().__init__(max_response_bytes)
        self.chat_id = chat_id
        self.confirmation_actions: tuple[dict[str, JSONValue], ...] = ()

    @property
    def requires_confirmation(self) -> bool:
        """Return whether a validated pending action block was received.
        """
        return bool(self.confirmation_actions)

    @property
    def received_bytes(self) -> int:
        """Return bytes charged to this turn's inbound text budget.
        """
        return self._received_bytes

    def feed(self, chunk: str) -> None:
        """Reject unsolicited trailing messages instead of dropping buffered data.
        """
        super().feed(chunk)
        if self.completed and self._pending.strip():
            raise RancherAIProtocolError("Unexpected data after </message>")

    def _consume_text(self) -> bool:
        """Recognize confirmation controls without changing global one-shot markers.
        """
        position = self._pending.find("<")
        if position == -1:
            self._append_text(self._pending)
            self._pending = ""
            return True
        if position:
            self._append_text(self._pending[:position])
            self._pending = self._pending[position:]
            return True

        for marker in _CONFIRMATION_MARKERS:
            if not self._pending.startswith(marker):
                continue
            self._pending = self._pending[len(marker):]
            if marker == "<message>":
                if self._started:
                    raise RancherAIProtocolError("Duplicate <message> marker")
                self._started = True
            elif marker == "</message>":
                if not self._started:
                    raise RancherAIProtocolError("Closing marker without <message>")
                if not self.answer.strip() and not self.requires_confirmation:
                    raise RancherAIIncompleteResponseError("Completed message without answer text")
                self.completed = True
            elif marker.startswith("</"):
                raise RancherAIProtocolError("Unmatched control closing marker")
            else:
                tag = marker[1:-1]
                if tag == _CONFIRMATION_TAG:
                    if not self._started:
                        raise RancherAIProtocolError("Confirmation outside <message>")
                    if self.requires_confirmation:
                        raise RancherAIConfirmationError(
                            "Multiple confirmation blocks in one turn",
                        )
                self._control_tag = tag
                self._scan_position = 0
                self._in_string = False
                self._escaped = False
            return True

        if any(marker.startswith(self._pending) for marker in _CONFIRMATION_MARKERS):
            return False
        self._append_text("<")
        self._pending = self._pending[1:]
        return True

    def _record_control(self, raw: str) -> None:
        """Validate pending actions and stable chat metadata after bounded JSON parsing.
        """
        try:
            json.loads(raw, object_pairs_hook=_unique_object, parse_float=_finite_float)
        except (ValueError, RecursionError):
            raise RancherAIProtocolError("Invalid or ambiguous JSON control block") from None
        previous_chat_id = self.chat_id
        super()._record_control(raw)
        event = self.events[-1]
        if event.tag == "chat-metadata":
            current = self.chat_id
            if previous_chat_id and current and current != previous_chat_id:
                self.chat_id = previous_chat_id
                raise RancherAIProtocolError("Chat identifier changed during the conversation")
            self.chat_id = current or previous_chat_id
        elif event.tag == _CONFIRMATION_TAG:
            data = event.data
            actions = [data] if isinstance(data, dict) else data
            if not isinstance(actions, list) or not actions:
                raise RancherAIProtocolError("Confirmation must contain nonempty action objects")
            for action in actions:
                if not isinstance(action, dict):
                    raise RancherAIProtocolError("Invalid confirmation action")
                action_type = action.get("type")
                if not isinstance(action_type, str) or not action_type.strip():
                    raise RancherAIProtocolError("Confirmation action requires a nonempty type")
                for key in ("payload", "resource"):
                    if key in action and not isinstance(action[key], dict):
                        raise RancherAIProtocolError("Invalid confirmation action object")
            self.confirmation_actions = tuple(cast(list[dict[str, JSONValue]], actions))
