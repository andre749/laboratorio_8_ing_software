"""Unit tests for the centralized JSON serializer."""

import json

import pytest

from shared.messaging.events import DinnerEvent, RewardProcessedEvent
from shared.messaging.serialization import SerializationError, deserialize, serialize


def _dinner() -> DinnerEvent:
    return DinnerEvent(
        transaction_id="tx-001",
        amount=85.5,
        card_number="4111111111111111",
        restaurant_code="REST-001",
        timestamp="2026-05-30T20:00:00Z",
    )


class TestSerialize:
    def test_produces_valid_utf8_json(self):
        payload = serialize(_dinner())
        data = json.loads(payload.decode("utf-8"))
        assert data["amount"] == 85.5
        assert data["transaction_id"] == "tx-001"


class TestDeserialize:
    def test_round_trip_dinner_event(self):
        event = _dinner()
        restored = deserialize(serialize(event), DinnerEvent)
        assert restored == event

    def test_round_trip_reward_processed_event(self):
        event = RewardProcessedEvent(
            transaction_id="tx-001",
            card_number="4111111111111111",
            points=85,
            cashback=4.275,
            restaurant_code="REST-001",
            timestamp="2026-05-30T20:00:00Z",
        )
        restored = deserialize(serialize(event), RewardProcessedEvent)
        assert restored == event

    def test_invalid_json_raises_serialization_error(self):
        with pytest.raises(SerializationError, match="Invalid event payload"):
            deserialize(b"not-json", DinnerEvent)

    def test_missing_field_raises_serialization_error(self):
        payload = json.dumps({"amount": 50.0}).encode()
        with pytest.raises(SerializationError, match="Invalid event payload"):
            deserialize(payload, DinnerEvent)

    def test_empty_bytes_raises_serialization_error(self):
        with pytest.raises(SerializationError):
            deserialize(b"", DinnerEvent)
