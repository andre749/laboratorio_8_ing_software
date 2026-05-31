"""Unit tests for RewardCalculator business rules."""

import pytest

from rewards_service.domain.restaurant import Restaurant, PREMIUM, STANDARD
from rewards_service.domain.reward_calculator import (
    MIN_AMOUNT,
    PREMIUM_CASHBACK_RATE,
    STANDARD_CASHBACK_RATE,
    RewardCalculator,
)


def _premium(code="REST-001") -> Restaurant:
    return Restaurant(code=code, name="La Trattoria", category=PREMIUM, active=True)


def _standard(code="REST-002") -> Restaurant:
    return Restaurant(code=code, name="Cafe Central", category=STANDARD, active=True)


@pytest.fixture()
def calc() -> RewardCalculator:
    return RewardCalculator()


class TestMinimumAmount:
    def test_below_minimum_returns_zero_reward(self, calc):
        reward = calc.calculate(MIN_AMOUNT - 0.01, _premium())
        assert reward.points == 0
        assert reward.cashback == 0.0

    def test_exactly_minimum_earns_reward(self, calc):
        reward = calc.calculate(MIN_AMOUNT, _premium())
        assert reward.is_positive

    def test_zero_amount_returns_zero_reward(self, calc):
        reward = calc.calculate(0.0, _premium())
        assert reward.points == 0
        assert reward.cashback == 0.0


class TestPointsCalculation:
    def test_integer_amount_gives_exact_points(self, calc):
        reward = calc.calculate(85.0, _premium())
        assert reward.points == 85

    def test_fractional_amount_truncates_points(self, calc):
        reward = calc.calculate(85.99, _premium())
        assert reward.points == 85

    def test_large_amount(self, calc):
        reward = calc.calculate(500.0, _standard())
        assert reward.points == 500


class TestCashbackCalculation:
    def test_premium_restaurant_applies_premium_rate(self, calc):
        reward = calc.calculate(100.0, _premium())
        assert reward.cashback == round(100.0 * PREMIUM_CASHBACK_RATE, 2)

    def test_standard_restaurant_applies_standard_rate(self, calc):
        reward = calc.calculate(100.0, _standard())
        assert reward.cashback == round(100.0 * STANDARD_CASHBACK_RATE, 2)

    def test_cashback_is_rounded_to_two_decimals(self, calc):
        reward = calc.calculate(33.33, _premium())
        assert reward.cashback == round(33.33 * PREMIUM_CASHBACK_RATE, 2)
