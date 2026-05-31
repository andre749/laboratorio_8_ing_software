"""Unit tests for the ProcessDinner use case (all dependencies mocked)."""

from unittest.mock import MagicMock

import pytest

from rewards_service.application.ports import (
    AccountRepository,
    NotificationPublisher,
    RestaurantRepository,
)
from rewards_service.application.process_dinner import ProcessDinner
from rewards_service.domain.restaurant import Restaurant, PREMIUM, STANDARD
from rewards_service.domain.reward import Reward
from shared.messaging.events import DinnerEvent


# ---------- helpers ----------------------------------------------------------

def _dinner(transaction_id="tx-001", amount=100.0, restaurant_code="REST-001") -> DinnerEvent:
    return DinnerEvent(
        transaction_id=transaction_id,
        amount=amount,
        card_number="4111111111111111",
        restaurant_code=restaurant_code,
        timestamp="2026-05-30T20:00:00Z",
    )


def _restaurant(active=True, category=PREMIUM) -> Restaurant:
    return Restaurant(code="REST-001", name="La Trattoria", category=category, active=active)


def _use_case(
    restaurant: Restaurant | None = None,
    already_processed: bool = False,
) -> tuple[ProcessDinner, MagicMock, MagicMock, MagicMock]:
    restaurants = MagicMock(spec=RestaurantRepository)
    restaurants.find.return_value = restaurant if restaurant is not None else _restaurant()

    accounts = MagicMock(spec=AccountRepository)
    accounts.is_transaction_processed.return_value = already_processed

    notifications = MagicMock(spec=NotificationPublisher)

    uc = ProcessDinner(
        restaurants=restaurants,
        accounts=accounts,
        notifications=notifications,
    )
    return uc, restaurants, accounts, notifications


# ---------- tests ------------------------------------------------------------

class TestDuplicateTransactions:
    def test_already_processed_returns_none(self):
        uc, _, accounts, notifications = _use_case(already_processed=True)
        result = uc.execute(_dinner())
        assert result is None
        accounts.add_reward.assert_not_called()
        notifications.publish.assert_not_called()


class TestUnaffiliatedOrInactiveRestaurant:
    def test_unknown_restaurant_returns_none(self):
        uc, restaurants, accounts, _ = _use_case(restaurant=None)
        restaurants.find.return_value = None
        result = uc.execute(_dinner())
        assert result is None
        accounts.add_reward.assert_not_called()

    def test_inactive_restaurant_returns_none(self):
        uc, _, accounts, _ = _use_case(restaurant=_restaurant(active=False))
        result = uc.execute(_dinner())
        assert result is None
        accounts.add_reward.assert_not_called()


class TestBelowMinimumAmount:
    def test_amount_below_minimum_returns_none_and_does_not_credit(self):
        uc, _, accounts, notifications = _use_case()
        result = uc.execute(_dinner(amount=5.0))
        assert result is None
        accounts.add_reward.assert_not_called()
        notifications.publish.assert_not_called()


class TestSuccessfulProcessing:
    def test_returns_notification_event(self):
        uc, _, _, _ = _use_case()
        result = uc.execute(_dinner(amount=100.0))
        assert result is not None
        assert result.card_number == "4111111111111111"
        assert result.restaurant_code == "REST-001"
        assert result.transaction_id == "tx-001"

    def test_add_reward_called_with_transaction_id(self):
        uc, _, accounts, _ = _use_case()
        uc.execute(_dinner(amount=100.0, transaction_id="tx-42"))
        accounts.add_reward.assert_called_once()
        call_args = accounts.add_reward.call_args
        assert call_args.args[1] == "tx-42"

    def test_notification_published_once(self):
        uc, _, _, notifications = _use_case()
        uc.execute(_dinner(amount=100.0))
        notifications.publish.assert_called_once()

    def test_premium_reward_uses_premium_cashback(self):
        uc, _, _, notifications = _use_case(restaurant=_restaurant(category=PREMIUM))
        result = uc.execute(_dinner(amount=100.0))
        assert result.cashback == 5.0

    def test_standard_reward_uses_standard_cashback(self):
        uc, _, _, notifications = _use_case(restaurant=_restaurant(category=STANDARD))
        result = uc.execute(_dinner(amount=100.0))
        assert result.cashback == 2.0

    def test_points_equal_floor_of_amount(self):
        uc, _, _, _ = _use_case()
        result = uc.execute(_dinner(amount=85.99))
        assert result.points == 85
