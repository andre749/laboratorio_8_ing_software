"""Integration tests for SqliteAccountRepository using a temporary SQLite file.

Note: ``:memory:`` cannot be used here because each call to ``sqlite3.connect``
opens an independent in-memory database, so the schema would be missing on
subsequent calls from the repository.  A NamedTemporaryFile gives a real path
that is shared across all ``connect`` calls within a test.
"""

import os
import tempfile

import sqlite3
from unittest.mock import patch

import pytest

from rewards_service.application.ports import RepositoryError
from rewards_service.domain.reward import Reward
from rewards_service.infrastructure.database import init_db
from rewards_service.infrastructure.sqlite_account_repository import SqliteAccountRepository


@pytest.fixture()
def repo() -> SqliteAccountRepository:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    init_db(db_path)
    yield SqliteAccountRepository(db_path)
    os.unlink(db_path)


class TestIsTransactionProcessed:
    def test_unknown_transaction_returns_false(self, repo):
        assert repo.is_transaction_processed("tx-unknown") is False

    def test_processed_transaction_returns_true(self, repo):
        repo.add_reward("4111111111111111", "tx-001", Reward(points=10, cashback=1.0))
        assert repo.is_transaction_processed("tx-001") is True


class TestAddReward:
    def test_creates_account_on_first_reward(self, repo):
        repo.add_reward("4111111111111111", "tx-001", Reward(points=50, cashback=2.5))
        balance = repo.get_balance("4111111111111111")
        assert balance is not None
        assert balance.points == 50
        assert balance.cashback == 2.5

    def test_accumulates_across_multiple_transactions(self, repo):
        repo.add_reward("4111111111111111", "tx-001", Reward(points=50, cashback=2.5))
        repo.add_reward("4111111111111111", "tx-002", Reward(points=30, cashback=1.5))
        balance = repo.get_balance("4111111111111111")
        assert balance.points == 80
        assert balance.cashback == pytest.approx(4.0)

    def test_different_cards_have_independent_accounts(self, repo):
        repo.add_reward("4111111111111111", "tx-001", Reward(points=50, cashback=2.5))
        repo.add_reward("5111111111111118", "tx-002", Reward(points=20, cashback=1.0))
        assert repo.get_balance("4111111111111111").points == 50
        assert repo.get_balance("5111111111111118").points == 20


class TestGetBalance:
    def test_returns_none_for_unknown_card(self, repo):
        assert repo.get_balance("9999999999999") is None

    def test_returns_reward_for_known_card(self, repo):
        repo.add_reward("4111111111111111", "tx-001", Reward(points=10, cashback=0.5))
        result = repo.get_balance("4111111111111111")
        assert isinstance(result, Reward)


class TestRepositoryErrors:
    def test_is_transaction_processed_raises_on_sqlite_error(self, repo):
        with patch(
            "rewards_service.infrastructure.database.connect",
            side_effect=sqlite3.Error("forced error"),
        ):
            with pytest.raises(RepositoryError, match="could not check transaction"):
                repo.is_transaction_processed("tx-001")

    def test_add_reward_raises_on_sqlite_error(self, repo):
        with patch(
            "rewards_service.infrastructure.database.connect",
            side_effect=sqlite3.Error("forced error"),
        ):
            with pytest.raises(RepositoryError, match="could not update account"):
                repo.add_reward("4111111111111111", "tx-001", Reward(points=10, cashback=0.5))

    def test_get_balance_raises_on_sqlite_error(self, repo):
        with patch(
            "rewards_service.infrastructure.database.connect",
            side_effect=sqlite3.Error("forced error"),
        ):
            with pytest.raises(RepositoryError, match="could not query account"):
                repo.get_balance("4111111111111111")
