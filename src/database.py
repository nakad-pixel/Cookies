from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS repositories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    last_scanned_at TEXT
);

CREATE TABLE IF NOT EXISTS cookies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repository_id INTEGER NOT NULL,
    domain TEXT NOT NULL,
    cookie_name TEXT NOT NULL,
    value_encrypted TEXT NOT NULL,
    expires_at TEXT,
    last_validated_at TEXT,
    FOREIGN KEY(repository_id) REFERENCES repositories(id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    event_payload TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    status TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


@dataclass
class Repository:
    name: str
    url: str
    last_scanned_at: Optional[str] = None


class Database:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with self._connection() as conn:
            conn.executescript(SCHEMA)
            conn.execute(
                "INSERT OR IGNORE INTO state (id, status, updated_at) VALUES (1, 'IDLE', datetime('now'))"
            )

    @contextmanager
    def _connection(self) -> Iterable[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def add_repository(self, repo: Repository) -> int:
        with self._connection() as conn:
            cursor = conn.execute(
                "INSERT INTO repositories (name, url, last_scanned_at) VALUES (?, ?, ?)",
                (repo.name, repo.url, repo.last_scanned_at),
            )
            return int(cursor.lastrowid)

    def list_repositories(self) -> list[Repository]:
        with self._connection() as conn:
            rows = conn.execute("SELECT name, url, last_scanned_at FROM repositories").fetchall()
        return [Repository(name=row[0], url=row[1], last_scanned_at=row[2]) for row in rows]

    def set_state(self, status: str) -> None:
        with self._connection() as conn:
            conn.execute(
                "UPDATE state SET status = ?, updated_at = datetime('now') WHERE id = 1",
                (status,),
            )

    def get_state(self) -> str:
        with self._connection() as conn:
            row = conn.execute("SELECT status FROM state WHERE id = 1").fetchone()
        return row[0] if row else "UNKNOWN"

    def add_audit_event(self, event_type: str, payload: str) -> None:
        with self._connection() as conn:
            conn.execute(
                "INSERT INTO audit_log (event_type, event_payload, created_at) VALUES (?, ?, datetime('now'))",
                (event_type, payload),
            )
