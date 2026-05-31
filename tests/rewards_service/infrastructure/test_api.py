"""Unit tests for the rewards service REST API."""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from rewards_service.application.ports import AccountRepository, RepositoryError
from rewards_service.domain.reward import Reward
from rewards_service.infrastructure.api import create_app


@pytest.fixture()
def accounts() -> MagicMock:
    return MagicMock(spec=AccountRepository)


@pytest.fixture()
def client(accounts) -> TestClient:
    return TestClient(create_app(accounts))


class TestGetBalance:
    def test_returns_200_with_balance(self, client, accounts):
        accounts.get_balance.return_value = Reward(points=85, cashback=4.25)
        response = client.get("/rewards/4111111111111111")
        assert response.status_code == 200
        data = response.json()
        assert data["card_number"] == "4111111111111111"
        assert data["total_points"] == 85
        assert data["total_cashback"] == 4.25

    def test_returns_404_for_unknown_card(self, client, accounts):
        accounts.get_balance.return_value = None
        response = client.get("/rewards/9999999999999")
        assert response.status_code == 404

    def test_returns_503_on_repository_error(self, client, accounts):
        accounts.get_balance.side_effect = RepositoryError("db error")
        response = client.get("/rewards/4111111111111111")
        assert response.status_code == 503
