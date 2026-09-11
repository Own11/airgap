import sqlite3
from pathlib import Path
from typing import Any

from app.config import Settings, get_settings


class SQLiteDatabase:
    def __init__(self, config: Settings | None = None) -> None:
        self.config = config or get_settings()

    def initialize(self) -> None:
        self.config.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.config.sqlite_path) as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS meetings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'uploaded',
                    language TEXT,
                    duration REAL,
                    transcript_json TEXT,
                    protocol_json TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )"""
            )

    def create_meeting(self, filename: str, file_path: Path) -> int:
        with sqlite3.connect(self.config.sqlite_path) as connection:
            cursor = connection.execute(
                "INSERT INTO meetings (filename, file_path) VALUES (?, ?)",
                (filename, str(file_path)),
            )
            return int(cursor.lastrowid)

    def list_meetings(self) -> list[dict[str, Any]]:
        with sqlite3.connect(self.config.sqlite_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                "SELECT id, filename, status, language, duration, created_at "
                "FROM meetings ORDER BY created_at DESC"
            ).fetchall()
            return [dict(row) for row in rows]
