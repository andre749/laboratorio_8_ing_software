"""SQLite implementation of ``RestaurantRepository``."""

from __future__ import annotations

import sqlite3

from rewards_service.application.ports import RepositoryError, RestaurantRepository
from rewards_service.domain.restaurant import Restaurant
from rewards_service.infrastructure.database import db_connection


class SqliteRestaurantRepository(RestaurantRepository):
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    def find(self, code: str) -> Restaurant | None:
        try:
            with db_connection(self._db_path) as conn:
                row = conn.execute(
                    "SELECT code, name, category, active "
                    "FROM restaurants WHERE code = ?",
                    (code,),
                ).fetchone()
        except sqlite3.Error as exc:
            raise RepositoryError(f"could not query restaurant: {exc}") from exc

        if row is None:
            return None
        return Restaurant(
            code=row[0], name=row[1], category=row[2], active=bool(row[3])
        )
