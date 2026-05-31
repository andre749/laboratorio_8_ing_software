"""Affiliated restaurant entity (rewards domain)."""

from __future__ import annotations

from dataclasses import dataclass

PREMIUM = "premium"
STANDARD = "estandar"


@dataclass(frozen=True)
class Restaurant:
    """A restaurant affiliated to the rewards program."""

    code: str
    name: str
    category: str
    active: bool

    @property
    def is_premium(self) -> bool:
        return self.category == PREMIUM
