"""Unit tests for the Reward value object."""

from rewards_service.domain.reward import Reward


class TestRewardIsPositive:
    def test_positive_when_only_points(self):
        assert Reward(points=10, cashback=0.0).is_positive

    def test_positive_when_only_cashback(self):
        assert Reward(points=0, cashback=1.5).is_positive

    def test_positive_when_both(self):
        assert Reward(points=5, cashback=2.5).is_positive

    def test_not_positive_when_both_zero(self):
        assert not Reward(points=0, cashback=0.0).is_positive
