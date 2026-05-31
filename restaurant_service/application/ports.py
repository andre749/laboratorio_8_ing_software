"""Output ports of the restaurant service (application layer).

These abstractions keep the use cases decoupled from the messaging technology:
the application depends on ``DinnerEventPublisher``, not on pika/RabbitMQ.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.messaging.events import DinnerEvent


class PublishError(RuntimeError):
    """Raised when an event cannot be published to the broker."""


class DinnerEventPublisher(ABC):
    """Port for publishing dinner events to the messaging broker."""

    @abstractmethod
    def publish(self, event: DinnerEvent) -> None:
        """Publish a dinner event. Raises ``PublishError`` on failure."""
