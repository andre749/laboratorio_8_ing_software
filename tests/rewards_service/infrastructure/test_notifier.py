"""Unit tests for Notifier.on_message (no live broker needed)."""

import json
from unittest.mock import MagicMock

from rewards_service.infrastructure.notifier import Notifier
from shared.messaging.topology import BrokerSettings

_SETTINGS = BrokerSettings(host="localhost", port=5672, user="u", password="p", virtual_host="/")


def _valid_body() -> bytes:
    return json.dumps({
        "transaction_id": "tx-001",
        "card_number": "4111111111111111",
        "points": 85,
        "cashback": 4.25,
        "restaurant_code": "REST-001",
        "timestamp": "2026-05-30T20:00:00Z",
    }).encode()


class TestNotifierOnMessage:
    def test_acks_valid_notification(self):
        channel = MagicMock()
        method = MagicMock()
        method.delivery_tag = 1
        Notifier(_SETTINGS).on_message(channel, method, None, _valid_body())
        channel.basic_ack.assert_called_once_with(delivery_tag=1)

    def test_malformed_message_is_acked_and_discarded(self):
        channel = MagicMock()
        method = MagicMock()
        method.delivery_tag = 2
        Notifier(_SETTINGS).on_message(channel, method, None, b"bad-json")
        channel.basic_ack.assert_called_once_with(delivery_tag=2)
