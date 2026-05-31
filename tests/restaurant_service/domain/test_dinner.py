"""Unit tests for the Dinner entity and its invariants."""

import pytest

from restaurant_service.domain.dinner import Dinner, DinnerValidationError

VALID_CARD = "4111111111111111"
VALID_CODE = "REST-001"
VALID_TS = "2026-05-30T20:00:00Z"


def _make(**kwargs) -> Dinner:
    defaults = dict(amount=50.0, card_number=VALID_CARD, restaurant_code=VALID_CODE, timestamp=VALID_TS)
    defaults.update(kwargs)
    return Dinner(**defaults)


class TestDinnerValidAmount:
    def test_positive_amount_is_accepted(self):
        dinner = _make(amount=10.0)
        assert dinner.amount == 10.0

    def test_zero_amount_raises(self):
        with pytest.raises(DinnerValidationError, match="amount must be greater than zero"):
            _make(amount=0.0)

    def test_negative_amount_raises(self):
        with pytest.raises(DinnerValidationError, match="amount must be greater than zero"):
            _make(amount=-5.0)


class TestDinnerCardNumber:
    def test_13_digits_is_accepted(self):
        dinner = _make(card_number="1234567890123")
        assert dinner.card_number == "1234567890123"

    def test_19_digits_is_accepted(self):
        dinner = _make(card_number="1234567890123456789")
        assert dinner.card_number == "1234567890123456789"

    def test_card_too_short_raises(self):
        with pytest.raises(DinnerValidationError, match="between 13 and 19 digits"):
            _make(card_number="123456789012")

    def test_card_too_long_raises(self):
        with pytest.raises(DinnerValidationError, match="between 13 and 19 digits"):
            _make(card_number="12345678901234567890")

    def test_card_with_letters_raises(self):
        with pytest.raises(DinnerValidationError, match="only digits"):
            _make(card_number="411111111111111A")

    def test_card_with_spaces_raises(self):
        with pytest.raises(DinnerValidationError, match="only digits"):
            _make(card_number="4111 1111 1111 1111")


class TestDinnerRestaurantCode:
    def test_empty_restaurant_code_raises(self):
        with pytest.raises(DinnerValidationError, match="restaurant_code must not be empty"):
            _make(restaurant_code="")

    def test_whitespace_restaurant_code_raises(self):
        with pytest.raises(DinnerValidationError, match="restaurant_code must not be empty"):
            _make(restaurant_code="   ")


class TestDinnerTimestamp:
    def test_empty_timestamp_raises(self):
        with pytest.raises(DinnerValidationError, match="timestamp must not be empty"):
            _make(timestamp="")

    def test_whitespace_timestamp_raises(self):
        with pytest.raises(DinnerValidationError, match="timestamp must not be empty"):
            _make(timestamp="   ")
