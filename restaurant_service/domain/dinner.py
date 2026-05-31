"""Dinner entity and its invariants (producer domain).

The producer validates the structural business rules it can check on its own:
positive amount (RN-03) and a well formed card number (RN-05). Whether the
restaurant is affiliated and active (RN-04) is owned by the rewards service,
which holds the restaurant catalog, so it is intentionally not checked here.
"""

from __future__ import annotations

from dataclasses import dataclass

_MIN_CARD_DIGITS = 13
_MAX_CARD_DIGITS = 19


class DinnerValidationError(ValueError):
    """Raised when the data of a dinner violates a business rule."""


@dataclass(frozen=True)
class Dinner:
    """A dinner consumed by a customer at an affiliated restaurant."""

    amount: float
    card_number: str
    restaurant_code: str
    timestamp: str

    def __post_init__(self) -> None:
        self._validate_amount()
        self._validate_card_number()
        self._validate_restaurant_code()
        self._validate_timestamp()

    def _validate_amount(self) -> None:
        if self.amount <= 0:
            raise DinnerValidationError("amount must be greater than zero")

    def _validate_card_number(self) -> None:
        if not self.card_number.isdigit():
            raise DinnerValidationError("card_number must contain only digits")
        if not _MIN_CARD_DIGITS <= len(self.card_number) <= _MAX_CARD_DIGITS:
            raise DinnerValidationError(
                f"card_number must have between {_MIN_CARD_DIGITS} and "
                f"{_MAX_CARD_DIGITS} digits"
            )

    def _validate_restaurant_code(self) -> None:
        if not self.restaurant_code.strip():
            raise DinnerValidationError("restaurant_code must not be empty")

    def _validate_timestamp(self) -> None:
        if not self.timestamp.strip():
            raise DinnerValidationError("timestamp must not be empty")
