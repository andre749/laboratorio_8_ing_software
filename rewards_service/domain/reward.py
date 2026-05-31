"""Reward value object (rewards domain)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Reward:
    """Points and cashback granted for a dinner (or an accumulated balance)."""

    points: int
    cashback: float

    @property
    def is_positive(self) -> bool:
        return self.points > 0 or self.cashback > 0
