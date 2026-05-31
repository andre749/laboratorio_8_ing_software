"""Event contracts exchanged through the broker.

These dataclasses are pure data carriers (the messaging contract). They hold no
business logic so the producer and consumer domains stay decoupled: each service
owns its own rules and only shares the shape of the messages.

``to_dict`` / ``from_dict`` are generated via ``dataclasses.asdict`` to avoid
per-field boilerplate and prevent drift between fields and serialization.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any


def _from_dict(cls: type, data: dict[str, Any]):
    """Instantiate a frozen dataclass from a dict using only known fields."""
    known = {f.name for f in dataclasses.fields(cls)}
    return cls(**{k: v for k, v in data.items() if k in known})


@dataclass(frozen=True)
class DinnerEvent:
    """A dinner registered by an affiliated restaurant (``cena.registrada``)."""

    transaction_id: str
    amount: float
    card_number: str
    restaurant_code: str
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DinnerEvent":
        return _from_dict(cls, data)


@dataclass(frozen=True)
class RewardProcessedEvent:
    """A reward credited to a customer account (``recompensa.procesada``)."""

    transaction_id: str
    card_number: str
    points: int
    cashback: float
    restaurant_code: str
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RewardProcessedEvent":
        return _from_dict(cls, data)
