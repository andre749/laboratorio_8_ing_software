"""Unit tests for the event contracts."""

from shared.messaging.events import DinnerEvent, RewardProcessedEvent


class TestDinnerEvent:
    def _event(self) -> DinnerEvent:
        return DinnerEvent(
            transaction_id="tx-001",
            amount=85.5,
            card_number="4111111111111111",
            restaurant_code="REST-001",
            timestamp="2026-05-30T20:00:00Z",
        )

    def test_to_dict_contains_all_fields(self):
        d = self._event().to_dict()
        assert d["transaction_id"] == "tx-001"
        assert d["amount"] == 85.5
        assert d["card_number"] == "4111111111111111"
        assert d["restaurant_code"] == "REST-001"
        assert d["timestamp"] == "2026-05-30T20:00:00Z"

    def test_round_trip_via_dict(self):
        original = self._event()
        restored = DinnerEvent.from_dict(original.to_dict())
        assert restored == original


class TestRewardProcessedEvent:
    def _event(self) -> RewardProcessedEvent:
        return RewardProcessedEvent(
            transaction_id="tx-001",
            card_number="4111111111111111",
            points=85,
            cashback=4.275,
            restaurant_code="REST-001",
            timestamp="2026-05-30T20:00:00Z",
        )

    def test_to_dict_contains_all_fields(self):
        d = self._event().to_dict()
        assert d["transaction_id"] == "tx-001"
        assert d["points"] == 85
        assert d["cashback"] == 4.275

    def test_round_trip_via_dict(self):
        original = self._event()
        restored = RewardProcessedEvent.from_dict(original.to_dict())
        assert restored == original
