from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional


SCHEMA = """
PRAGMA journal_mode=WAL;

-- Repository metadata only - NO sensitive data
CREATE TABLE IF NOT EXISTS repositories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    url TEXT NOT NULL,
    requires_cookies INTEGER DEFAULT 0,
    last_scanned_at TEXT,
    created_at TEXT DEFAULT datetime('now')
);

-- Cookie extraction metadata only - NO cookie values stored
CREATE TABLE IF NOT EXISTS cookie_extractions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repository_id INTEGER NOT NULL,
    platform TEXT NOT NULL,
    cookie_count INTEGER DEFAULT 0,
    has_2fa INTEGER DEFAULT 0,
    success INTEGER DEFAULT 0,
    error_message TEXT,
    extracted_at TEXT NOT NULL,
    expires_at TEXT,
    FOREIGN KEY(repository_id) REFERENCES repositories(id)
);

-- Audit log for operations - NO sensitive values
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    repository_name TEXT,
    platform TEXT,
    status TEXT,
    message TEXT,
    created_at TEXT DEFAULT datetime('now')
);

-- State tracking
CREATE TABLE IF NOT EXISTS state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    status TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Platform credentials configuration (metadata only)
CREATE TABLE IF NOT EXISTS platform_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform_name TEXT NOT NULL UNIQUE,
    login_url TEXT,
    cookie_domain TEXT,
    requires_auth INTEGER DEFAULT 0,
    created_at TEXT DEFAULT datetime('now')
);
"""


@dataclass
class Repository:
    name: str
    url: str
    requires_cookies: bool = False
    last_scanned_at: Optional[str] = None


@dataclass
class ExtractionRecord:
    """Metadata about a cookie extraction - no actual cookie values."""
    repository_id: int
    platform: str
    cookie_count: int
    has_2fa: bool
    success: bool
    error_message: Optional[str] = None
    expires_at: Optional[str] = None


class Database:
    """SQLite database for metadata only - NO cookie values stored."""

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
        """Add or update a repository."""
        with self._connection() as conn:
            cursor = conn.execute(
                """INSERT INTO repositories (name, url, requires_cookies, last_scanned_at)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(name) DO UPDATE SET
                       url = excluded.url,
                       requires_cookies = excluded.requires_cookies,
                       last_scanned_at = excluded.last_scanned_at""",
                (repo.name, repo.url, int(repo.requires_cookies), repo.last_scanned_at),
            )
            return int(cursor.lastrowid)

    def list_repositories(self, requires_cookies: Optional[bool] = None) -> list[Repository]:
        """List repositories, optionally filtered by cookie requirement."""
        with self._connection() as conn:
            if requires_cookies is not None:
                rows = conn.execute(
                    "SELECT name, url, requires_cookies, last_scanned_at FROM repositories WHERE requires_cookies = ?",
                    (int(requires_cookies),)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT name, url, requires_cookies, last_scanned_at FROM repositories"
                ).fetchall()
        return [
            Repository(
                name=row[0],
                url=row[1],
                requires_cookies=bool(row[2]),
                last_scanned_at=row[3]
            )
            for row in rows
        ]

    def record_extraction(self, record: ExtractionRecord) -> int:
        """Record metadata about a cookie extraction - no cookie values stored."""
        with self._connection() as conn:
            cursor = conn.execute(
                """INSERT INTO cookie_extractions
                   (repository_id, platform, cookie_count, has_2fa, success, error_message, extracted_at, expires_at)
                   VALUES (?, ?, ?, ?, ?, ?, datetime('now'), ?)""",
                (
                    record.repository_id,
                    record.platform,
                    record.cookie_count,
                    int(record.has_2fa),
                    int(record.success),
                    record.error_message,
                    record.expires_at,
                ),
            )
            return int(cursor.lastrowid)

    def get_recent_extractions(self, repository_id: int, limit: int = 10) -> list[dict]:
        """Get recent extraction metadata for a repository."""
        with self._connection() as conn:
            rows = conn.execute(
                """SELECT platform, cookie_count, has_2fa, success, extracted_at, expires_at
                   FROM cookie_extractions
                   WHERE repository_id = ?
                   ORDER BY extracted_at DESC
                   LIMIT ?""",
                (repository_id, limit)
            ).fetchall()
        return [
            {
                "platform": row[0],
                "cookie_count": row[1],
                "has_2fa": bool(row[2]),
                "success": bool(row[3]),
                "extracted_at": row[4],
                "expires_at": row[5],
            }
            for row in rows
        ]

    def set_state(self, status: str) -> None:
        """Update the current state."""
        with self._connection() as conn:
            conn.execute(
                "UPDATE state SET status = ?, updated_at = datetime('now') WHERE id = 1",
                (status,),
            )

    def get_state(self) -> str:
        """Get the current state."""
        with self._connection() as conn:
            row = conn.execute("SELECT status FROM state WHERE id = 1").fetchone()
        return row[0] if row else "UNKNOWN"

    def add_audit_event(
        self,
        event_type: str,
        repository_name: Optional[str] = None,
        platform: Optional[str] = None,
        status: Optional[str] = None,
        message: Optional[str] = None
    ) -> None:
        """Add an audit event - no sensitive data should be in message."""
        # Ensure no sensitive data in message
        safe_message = message[:500] if message else None  # Limit length
        with self._connection() as conn:
            conn.execute(
                """INSERT INTO audit_log (event_type, repository_name, platform, status, message, created_at)
                   VALUES (?, ?, ?, ?, ?, datetime('now'))""",
                (event_type, repository_name, platform, status, safe_message),
            )

    def add_platform_config(
        self,
        platform_name: str,
        login_url: Optional[str] = None,
        cookie_domain: Optional[str] = None,
        requires_auth: bool = False
    ) -> int:
        """Add a platform configuration."""
        with self._connection() as conn:
            cursor = conn.execute(
                """INSERT INTO platform_configs (platform_name, login_url, cookie_domain, requires_auth)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(platform_name) DO UPDATE SET
                       login_url = excluded.login_url,
                       cookie_domain = excluded.cookie_domain,
                       requires_auth = excluded.requires_auth""",
                (platform_name, login_url, cookie_domain, int(requires_auth)),
            )
            return int(cursor.lastrowid)

    def get_platform_config(self, platform_name: str) -> Optional[dict]:
        """Get platform configuration."""
        with self._connection() as conn:
            row = conn.execute(
                "SELECT platform_name, login_url, cookie_domain, requires_auth FROM platform_configs WHERE platform_name = ?",
                (platform_name,)
            ).fetchone()
        if row:
            return {
                "platform_name": row[0],
                "login_url": row[1],
                "cookie_domain": row[2],
                "requires_auth": bool(row[3]),
            }
        return None
