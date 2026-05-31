"""Reward calculation rules (RN-02, RN-03, RN-04)."""

from __future__ import annotations

from rewards_service.domain.restaurant import Restaurant
from rewards_service.domain.reward import Reward

# RN-02: minimum spend to earn any reward.
MIN_AMOUNT = 10.0
# RN-03: 1 point per monetary unit consumed (integer part).
MONETARY_UNIT_PER_POINT = 1
# RN-04: cashback rate differs by restaurant category.
PREMIUM_CASHBACK_RATE = 0.05
STANDARD_CASHBACK_RATE = 0.02


class RewardCalculator:
    """Calculates the reward for a dinner based on its amount and restaurant."""

    def calculate(self, amount: float, restaurant: Restaurant) -> Reward:
        if amount < MIN_AMOUNT:
            return Reward(points=0, cashback=0.0)
        points = int(amount // MONETARY_UNIT_PER_POINT)
        rate = PREMIUM_CASHBACK_RATE if restaurant.is_premium else STANDARD_CASHBACK_RATE
        cashback = round(amount * rate, 2)
        return Reward(points=points, cashback=cashback)
