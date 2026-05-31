"""Centralized JSON (de)serialization for events.

Keeping a single serializer avoids duplicating encode/decode logic across the
producer and consumer (Duplications quality gate).
"""

from __future__ import annotations

import json
from typing import Any, Protocol


class _Event(Protocol):
    """Minimal contract a serializable event must satisfy."""

    def to_dict(self) -> dict[str, Any]: ...


class SerializationError(ValueError):
    """Raised when a payload cannot be decoded into a valid event."""


def serialize(event: _Event) -> bytes:
    """Encode an event into UTF-8 JSON bytes ready to publish."""
    return json.dumps(event.to_dict()).encode("utf-8")


def deserialize[T](payload: bytes, factory: type[T]) -> T:
    """Decode JSON bytes into an event using ``factory.from_dict``.

    Raises:
        SerializationError: if the payload is not valid JSON or is missing
            required fields.
    """
    try:
        data = json.loads(payload.decode("utf-8"))
        return factory.from_dict(data)  # type: ignore[attr-defined]
    except (json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError) as exc:
        raise SerializationError(f"Invalid event payload: {exc}") from exc
