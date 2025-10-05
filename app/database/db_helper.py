from __future__ import annotations

import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from app.misc.paths import Paths


class DatabaseManager:
    _db_path: Path = Paths.DATA_DIR / "pulser.db"
    _lock = threading.RLock()
    _initialized = False

    @classmethod
    def initialize(cls) -> None:
        with cls._lock:
            if cls._initialized:
                return
            Paths.ensure_directories()
            with sqlite3.connect(cls._db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                conn.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS channels (
                        channel_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        channel_type INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        url TEXT NOT NULL UNIQUE
                    );

                    CREATE TABLE IF NOT EXISTS posts (
                        post_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        channel_id INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        content TEXT,
                        link TEXT NOT NULL UNIQUE,
                        rating INTEGER NOT NULL,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY(channel_id) REFERENCES channels(channel_id) ON DELETE CASCADE
                    );

                    CREATE TABLE IF NOT EXISTS posts_hashtags (
                        hashtag_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        post_id INTEGER NOT NULL,
                        hashtag TEXT NOT NULL,
                        FOREIGN KEY(post_id) REFERENCES posts(post_id) ON DELETE CASCADE
                    );
                    """
                )
            cls._initialized = True

    @classmethod
    def connection(cls) -> sqlite3.Connection:
        cls.initialize()
        conn = sqlite3.connect(cls._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @classmethod
    def execute(cls, query: str, params: Iterable | None = None) -> None:
        with cls._lock:
            with cls.connection() as conn:
                conn.execute(query, tuple(params or ()))
                conn.commit()

    @classmethod
    def executemany(cls, query: str, params_seq: Iterable[Iterable]) -> None:
        with cls._lock:
            with cls.connection() as conn:
                conn.executemany(query, params_seq)
                conn.commit()

    @classmethod
    def fetchone(cls, query: str, params: Iterable | None = None) -> Optional[sqlite3.Row]:
        with cls._lock:
            with cls.connection() as conn:
                cur = conn.execute(query, tuple(params or ()))
                return cur.fetchone()

    @classmethod
    def fetchall(cls, query: str, params: Iterable | None = None) -> list[sqlite3.Row]:
        with cls._lock:
            with cls.connection() as conn:
                cur = conn.execute(query, tuple(params or ()))
                return cur.fetchall()

    @classmethod
    def is_exists(cls, table: str, column: str, value: object) -> bool:
        query = f"SELECT 1 FROM {table} WHERE {column} = ? LIMIT 1"
        return cls.fetchone(query, (value,)) is not None


class DatabaseHelper:
    """Compatibility shim for the legacy API."""

    def __init__(self) -> None:
        DatabaseManager.initialize()


@dataclass(slots=True)
class Channel:
    title: str
    url: str
    channel_type: int = 1
    channel_id: Optional[int] = field(default=None)

    def save(self) -> int:
        if self.channel_id is None:
            DatabaseManager.execute(
                "INSERT OR IGNORE INTO channels(channel_type, title, url) VALUES(?, ?, ?)",
                (self.channel_type, self.title, self.url),
            )
            row = DatabaseManager.fetchone(
                "SELECT channel_id FROM channels WHERE url = ?",
                (self.url,),
            )
            if row:
                self.channel_id = int(row["channel_id"])
        else:
            DatabaseManager.execute(
                "UPDATE channels SET channel_type = ?, title = ?, url = ? WHERE channel_id = ?",
                (self.channel_type, self.title, self.url, self.channel_id),
            )
        return self.channel_id or 0


@dataclass(slots=True)
class Post:
    channel_id: int
    title: str
    content: str
    link: str
    rating: int
    created_at: datetime = field(default_factory=datetime.utcnow)
    post_id: Optional[int] = field(default=None)

    def save(self) -> int:
        DatabaseManager.execute(
            """
            INSERT OR IGNORE INTO posts(channel_id, title, content, link, rating, created_at)
            VALUES(?, ?, ?, ?, ?, ?)
            """,
            (
                self.channel_id,
                self.title,
                self.content,
                self.link,
                self.rating,
                self.created_at.isoformat(timespec="seconds"),
            ),
        )
        row = DatabaseManager.fetchone(
            "SELECT post_id FROM posts WHERE link = ?",
            (self.link,),
        )
        if row:
            self.post_id = int(row["post_id"])
        return self.post_id or 0


__all__ = ["DatabaseManager", "DatabaseHelper", "Channel", "Post"]
