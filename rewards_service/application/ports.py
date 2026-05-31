"""Ports of the rewards service (application layer).

The use cases depend on these abstractions, not on SQLite or pika, keeping the
domain and application layers free of infrastructure details.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from rewards_service.domain.restaurant import Restaurant
from rewards_service.domain.reward import Reward
from shared.messaging.events import RewardProcessedEvent


class RepositoryError(RuntimeError):
    """Raised when a persistence operation fails."""


class PublishError(RuntimeError):
    """Raised when the notification event cannot be published."""


class RestaurantRepository(ABC):
    """Port to look up affiliated restaurants."""

    @abstractmethod
    def find(self, code: str) -> Restaurant | None:
        """Return the restaurant with the given code, or ``None`` if missing."""


class AccountRepository(ABC):
    """Port to persist and query customer reward accounts."""

    @abstractmethod
    def is_transaction_processed(self, transaction_id: str) -> bool:
        """Return True if this transaction was already credited (idempotence, RN-06)."""

    @abstractmethod
    def add_reward(self, card_number: str, transaction_id: str, reward: Reward) -> None:
        """Accumulate the reward and mark the transaction as processed."""

    @abstractmethod
    def get_balance(self, card_number: str) -> Reward | None:
        """Return the accumulated balance, or ``None`` if no account exists."""


class NotificationPublisher(ABC):
    """Port to publish the ``recompensa.procesada`` notification event."""

    @abstractmethod
    def publish(self, event: RewardProcessedEvent) -> None:
        """Publish the notification event. Raises ``PublishError`` on failure."""
