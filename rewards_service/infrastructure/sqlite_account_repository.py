"""SQLite implementation of ``AccountRepository`` (accumulates rewards)."""

from __future__ import annotations

import sqlite3

from rewards_service.application.ports import AccountRepository, RepositoryError
from rewards_service.domain.reward import Reward
from rewards_service.infrastructure.database import db_connection


class SqliteAccountRepository(AccountRepository):
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    def is_transaction_processed(self, transaction_id: str) -> bool:
        try:
            with db_connection(self._db_path) as conn:
                row = conn.execute(
                    "SELECT 1 FROM processed_transactions WHERE transaction_id = ?",
                    (transaction_id,),
                ).fetchone()
        except sqlite3.Error as exc:
            raise RepositoryError(f"could not check transaction: {exc}") from exc
        return row is not None

    def add_reward(self, card_number: str, transaction_id: str, reward: Reward) -> None:
        try:
            with db_connection(self._db_path) as conn:
                conn.execute(
                    "INSERT INTO processed_transactions "
                    "(transaction_id, card_number, processed_at) "
                    "VALUES (?, ?, datetime('now'))",
                    (transaction_id, card_number),
                )
                conn.execute(
                    "INSERT INTO accounts "
                    "(card_number, total_points, total_cashback) "
                    "VALUES (?, ?, ?) "
                    "ON CONFLICT(card_number) DO UPDATE SET "
                    "total_points = total_points + excluded.total_points, "
                    "total_cashback = total_cashback + excluded.total_cashback",
                    (card_number, reward.points, reward.cashback),
                )
                conn.commit()
        except sqlite3.Error as exc:
            raise RepositoryError(f"could not update account: {exc}") from exc

    def get_balance(self, card_number: str) -> Reward | None:
        try:
            with db_connection(self._db_path) as conn:
                row = conn.execute(
                    "SELECT total_points, total_cashback "
                    "FROM accounts WHERE card_number = ?",
                    (card_number,),
                ).fetchone()
        except sqlite3.Error as exc:
            raise RepositoryError(f"could not query account: {exc}") from exc

        if row is None:
            return None
        return Reward(points=row[0], cashback=row[1])
