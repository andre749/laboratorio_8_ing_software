"""SQLite schema creation, seed data, and connection helpers."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Generator

from rewards_service.domain.restaurant import PREMIUM, STANDARD

_SCHEMA = """
CREATE TABLE IF NOT EXISTS restaurants (
    code     TEXT PRIMARY KEY,
    name     TEXT NOT NULL,
    category TEXT NOT NULL,
    active   INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS accounts (
    card_number    TEXT PRIMARY KEY,
    total_points   INTEGER NOT NULL DEFAULT 0,
    total_cashback REAL    NOT NULL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS processed_transactions (
    transaction_id TEXT PRIMARY KEY,
    card_number    TEXT NOT NULL,
    processed_at   TEXT NOT NULL
);
"""

_SEED_RESTAURANTS = [
    ("REST-001", "La Trattoria", PREMIUM, 1),
    ("REST-002", "Cafe Central", STANDARD, 1),
    ("REST-003", "Bistro Norte", PREMIUM, 1),
    ("REST-004", "Antiguo Sabor", STANDARD, 0),
]


def connect(db_path: str) -> sqlite3.Connection:
    """Open a SQLite connection to the given path."""
    return sqlite3.connect(db_path)


@contextmanager
def db_connection(db_path: str) -> Generator[sqlite3.Connection, None, None]:
    """Context manager that opens, yields, and closes a SQLite connection."""
    connection = connect(db_path)
    try:
        yield connection
    finally:
        connection.close()


def init_db(db_path: str) -> None:
    """Create the schema and seed the restaurant catalog if not present."""
    with db_connection(db_path) as connection:
        connection.executescript(_SCHEMA)
        connection.executemany(
            "INSERT OR IGNORE INTO restaurants (code, name, category, active) "
            "VALUES (?, ?, ?, ?)",
            _SEED_RESTAURANTS,
        )
        connection.commit()
