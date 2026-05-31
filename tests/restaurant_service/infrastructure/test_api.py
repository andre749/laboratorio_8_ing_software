"""Unit tests for the restaurant service REST API."""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from restaurant_service.application.ports import DinnerEventPublisher, PublishError
from restaurant_service.application.register_dinner import RegisterDinner
from restaurant_service.domain.dinner import DinnerValidationError
from restaurant_service.infrastructure.api import create_app
from shared.messaging.events import DinnerEvent

_VALID_PAYLOAD = {
    "amount": 85.50,
    "card_number": "4111111111111111",
    "restaurant_code": "REST-001",
    "timestamp": "2026-05-30T20:00:00Z",
}


def _event(**overrides) -> DinnerEvent:
    defaults = dict(
        transaction_id="tx-001",
        amount=85.50,
        card_number="4111111111111111",
        restaurant_code="REST-001",
        timestamp="2026-05-30T20:00:00Z",
    )
    defaults.update(overrides)
    return DinnerEvent(**defaults)


@pytest.fixture()
def publisher() -> MagicMock:
    return MagicMock(spec=DinnerEventPublisher)


@pytest.fixture()
def client(publisher) -> TestClient:
    use_case = RegisterDinner(publisher)
    return TestClient(create_app(use_case))


class TestRegisterDinnerEndpoint:
    def test_valid_request_returns_202(self, client, publisher):
        publisher.publish.return_value = None
        response = client.post("/dinners", json=_VALID_PAYLOAD)
        assert response.status_code == 202

    def test_response_contains_restaurant_code(self, client):
        response = client.post("/dinners", json=_VALID_PAYLOAD)
        assert response.json()["restaurant_code"] == "REST-001"

    def test_response_status_is_accepted(self, client):
        response = client.post("/dinners", json=_VALID_PAYLOAD)
        assert response.json()["status"] == "accepted"

    def test_invalid_amount_returns_400(self, client):
        payload = {**_VALID_PAYLOAD, "amount": -10.0}
        response = client.post("/dinners", json=payload)
        assert response.status_code == 400

    def test_invalid_card_number_returns_400(self, client):
        payload = {**_VALID_PAYLOAD, "card_number": "123"}
        response = client.post("/dinners", json=payload)
        assert response.status_code == 400

    def test_empty_restaurant_code_returns_400(self, client):
        payload = {**_VALID_PAYLOAD, "restaurant_code": ""}
        response = client.post("/dinners", json=payload)
        assert response.status_code == 400

    def test_broker_unavailable_returns_503(self, client, publisher):
        publisher.publish.side_effect = PublishError("broker down")
        response = client.post("/dinners", json=_VALID_PAYLOAD)
        assert response.status_code == 503
