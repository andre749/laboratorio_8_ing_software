"""Unit tests for DinnerConsumer.on_message (no live broker needed)."""

import json
from unittest.mock import MagicMock, patch

from rewards_service.application.process_dinner import ProcessDinner
from rewards_service.infrastructure.rabbitmq_consumer import DinnerConsumer
from shared.messaging.topology import BrokerSettings

_SETTINGS = BrokerSettings(host="localhost", port=5672, user="u", password="p", virtual_host="/")


def _consumer(process_dinner=None) -> DinnerConsumer:
    return DinnerConsumer(_SETTINGS, process_dinner or MagicMock(spec=ProcessDinner))


def _method(tag=1):
    m = MagicMock()
    m.delivery_tag = tag
    return m


def _valid_body() -> bytes:
    return json.dumps({
        "transaction_id": "tx-001",
        "amount": 100.0,
        "card_number": "4111111111111111",
        "restaurant_code": "REST-001",
        "timestamp": "2026-05-30T20:00:00Z",
    }).encode()


class TestOnMessageSuccess:
    def test_acks_after_successful_processing(self):
        channel = MagicMock()
        method = _method()
        process = MagicMock(spec=ProcessDinner)
        _consumer(process).on_message(channel, method, None, _valid_body())
        channel.basic_ack.assert_called_once_with(delivery_tag=1)
        channel.basic_nack.assert_not_called()

    def test_process_dinner_called_once(self):
        channel = MagicMock()
        process = MagicMock(spec=ProcessDinner)
        _consumer(process).on_message(channel, _method(), None, _valid_body())
        process.execute.assert_called_once()


class TestOnMessageMalformed:
    def test_malformed_json_is_acked_and_discarded(self):
        channel = MagicMock()
        process = MagicMock(spec=ProcessDinner)
        _consumer(process).on_message(channel, _method(), None, b"bad-json")
        channel.basic_ack.assert_called_once()
        process.execute.assert_not_called()


class TestOnMessageProcessingError:
    def test_repository_error_nacks_with_requeue(self):
        from rewards_service.application.ports import RepositoryError
        channel = MagicMock()
        process = MagicMock(spec=ProcessDinner)
        process.execute.side_effect = RepositoryError("db error")
        _consumer(process).on_message(channel, _method(), None, _valid_body())
        channel.basic_nack.assert_called_once_with(delivery_tag=1, requeue=True)
        channel.basic_ack.assert_not_called()
