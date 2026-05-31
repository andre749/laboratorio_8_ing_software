"""Unit tests for the card number masking helper."""

from shared.messaging.security import mask_card_number


class TestMaskCardNumber:
    def test_standard_card_shows_last_four(self):
        assert mask_card_number("4111111111111111") == "************1111"

    def test_short_card_fully_masked(self):
        assert mask_card_number("123") == "***"

    def test_exactly_four_digits_fully_masked(self):
        assert mask_card_number("1234") == "****"

    def test_five_digits_shows_last_four(self):
        assert mask_card_number("12345") == "*2345"

    def test_none_returns_empty_string(self):
        assert mask_card_number(None) == ""

    def test_mask_length_equals_input_length(self):
        card = "4111111111111111"
        masked = mask_card_number(card)
        assert len(masked) == len(card)
