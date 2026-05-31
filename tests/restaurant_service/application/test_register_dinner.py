"""Unit tests for the RegisterDinner use case."""

from unittest.mock import MagicMock

import pytest

from restaurant_service.application.ports import DinnerEventPublisher, PublishError
from restaurant_service.application.register_dinner import (
    RegisterDinner,
    RegisterDinnerCommand,
)
from restaurant_service.domain.dinner import DinnerValidationError

_COMMAND = RegisterDinnerCommand(
    amount=85.50,
    card_number="4111111111111111",
    restaurant_code="REST-001",
    timestamp="2026-05-30T20:00:00Z",
)


def _use_case(publisher=None) -> RegisterDinner:
    return RegisterDinner(publisher or MagicMock(spec=DinnerEventPublisher))


class TestRegisterDinnerSuccess:
    def test_returns_event_with_correct_fields(self):
        publisher = MagicMock(spec=DinnerEventPublisher)
        event = _use_case(publisher).execute(_COMMAND)
        assert event.amount == 85.50
        assert event.card_number == "4111111111111111"
        assert event.restaurant_code == "REST-001"
        assert event.timestamp == "2026-05-30T20:00:00Z"

    def test_transaction_id_is_generated(self):
        event = _use_case().execute(_COMMAND)
        assert event.transaction_id is not None
        assert len(event.transaction_id) == 36  # UUID v4 format

    def test_each_execution_produces_unique_transaction_id(self):
        uc = _use_case()
        id1 = uc.execute(_COMMAND).transaction_id
        id2 = uc.execute(_COMMAND).transaction_id
        assert id1 != id2

    def test_publisher_is_called_once_with_event(self):
        publisher = MagicMock(spec=DinnerEventPublisher)
        event = RegisterDinner(publisher).execute(_COMMAND)
        publisher.publish.assert_called_once_with(event)


class TestRegisterDinnerValidation:
    def test_invalid_amount_raises_validation_error(self):
        bad = RegisterDinnerCommand(
            amount=-1.0,
            card_number="4111111111111111",
            restaurant_code="REST-001",
            timestamp="2026-05-30T20:00:00Z",
        )
        with pytest.raises(DinnerValidationError):
            _use_case().execute(bad)

    def test_invalid_card_number_raises_validation_error(self):
        bad = RegisterDinnerCommand(
            amount=50.0,
            card_number="short",
            restaurant_code="REST-001",
            timestamp="2026-05-30T20:00:00Z",
        )
        with pytest.raises(DinnerValidationError):
            _use_case().execute(bad)

    def test_publish_error_propagates(self):
        publisher = MagicMock(spec=DinnerEventPublisher)
        publisher.publish.side_effect = PublishError("broker down")
        with pytest.raises(PublishError):
            RegisterDinner(publisher).execute(_COMMAND)
