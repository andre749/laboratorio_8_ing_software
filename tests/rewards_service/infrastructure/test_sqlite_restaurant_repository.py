"""Integration tests for SqliteRestaurantRepository."""

import os
import tempfile

import pytest

from rewards_service.domain.restaurant import PREMIUM, STANDARD
from rewards_service.infrastructure.database import init_db
from rewards_service.infrastructure.sqlite_restaurant_repository import SqliteRestaurantRepository


@pytest.fixture()
def repo() -> SqliteRestaurantRepository:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    init_db(db_path)
    yield SqliteRestaurantRepository(db_path)
    os.unlink(db_path)


class TestFind:
    def test_returns_none_for_unknown_code(self, repo):
        assert repo.find("UNKNOWN") is None

    def test_returns_restaurant_for_known_code(self, repo):
        restaurant = repo.find("REST-001")
        assert restaurant is not None
        assert restaurant.code == "REST-001"
        assert restaurant.category == PREMIUM
        assert restaurant.active is True

    def test_returns_inactive_restaurant(self, repo):
        restaurant = repo.find("REST-004")
        assert restaurant is not None
        assert restaurant.active is False

    def test_standard_restaurant_category(self, repo):
        restaurant = repo.find("REST-002")
        assert restaurant.category == STANDARD


class TestFindRepositoryError:
    def test_raises_repository_error_on_sqlite_error(self, repo):
        import sqlite3
        from unittest.mock import patch
        from rewards_service.application.ports import RepositoryError
        with patch(
            "rewards_service.infrastructure.database.connect",
            side_effect=sqlite3.Error("forced error"),
        ):
            with pytest.raises(RepositoryError, match="could not query restaurant"):
                repo.find("REST-001")
