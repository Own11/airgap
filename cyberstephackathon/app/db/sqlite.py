import sqlite3
import json
from datetime import datetime, timezone
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
                    error_message TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )"""
            )
            columns = {row[1] for row in connection.execute("PRAGMA table_info(meetings)")}
            if "user_id" not in columns:
                connection.execute("ALTER TABLE meetings ADD COLUMN user_id INTEGER")
            if "error_message" not in columns:
                connection.execute("ALTER TABLE meetings ADD COLUMN error_message TEXT")

    def create_user(self, name: str, email: str, password_hash: str) -> int:
        with sqlite3.connect(self.config.sqlite_path) as connection:
            cursor = connection.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email.lower(), password_hash),
            )
            return int(cursor.lastrowid)

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        with sqlite3.connect(self.config.sqlite_path) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute("SELECT * FROM users WHERE email = ?", (email.lower(),)).fetchone()
            return dict(row) if row else None

    def create_session(self, token: str, user_id: int) -> None:
        with sqlite3.connect(self.config.sqlite_path) as connection:
            connection.execute(
                "INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)",
                (token, user_id, datetime.now(timezone.utc).isoformat()),
            )

    def get_user_by_session(self, token: str | None) -> dict[str, Any] | None:
        if not token:
            return None
        with sqlite3.connect(self.config.sqlite_path) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                "SELECT users.id, users.name, users.email FROM sessions JOIN users ON users.id = sessions.user_id WHERE sessions.token = ?",
                (token,),
            ).fetchone()
            return dict(row) if row else None

    def delete_session(self, token: str) -> None:
        with sqlite3.connect(self.config.sqlite_path) as connection:
            connection.execute("DELETE FROM sessions WHERE token = ?", (token,))

    def create_meeting(self, filename: str, file_path: Path, user_id: int | None = None) -> int:
        with sqlite3.connect(self.config.sqlite_path) as connection:
            cursor = connection.execute(
                "INSERT INTO meetings (filename, file_path, user_id) VALUES (?, ?, ?)",
                (filename, str(file_path), user_id),
            )
            return int(cursor.lastrowid)

    def list_meetings(self, user_id: int | None = None) -> list[dict[str, Any]]:
        with sqlite3.connect(self.config.sqlite_path) as connection:
            connection.row_factory = sqlite3.Row
            query = "SELECT id, filename, status, language, duration, created_at FROM meetings"
            params: tuple[Any, ...] = ()
            if user_id is not None:
                query += " WHERE user_id = ?"
                params = (user_id,)
            rows = connection.execute(query + " ORDER BY created_at DESC", params).fetchall()
            return [dict(row) for row in rows]

    def get_meeting(self, meeting_id: int) -> dict[str, Any] | None:
        with sqlite3.connect(self.config.sqlite_path) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,)).fetchone()
            return dict(row) if row else None

    def delete_meeting(self, meeting_id: int, user_id: int) -> str | None:
        with sqlite3.connect(self.config.sqlite_path) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                "SELECT file_path FROM meetings WHERE id = ? AND user_id = ?",
                (meeting_id, user_id),
            ).fetchone()
            if not row:
                return None
            connection.execute("DELETE FROM meetings WHERE id = ? AND user_id = ?", (meeting_id, user_id))
            return str(row["file_path"])

    def update_meeting(self, meeting_id: int, **fields: Any) -> None:
        allowed = {"status", "language", "duration", "transcript_json", "protocol_json", "error_message"}
        values = {key: value for key, value in fields.items() if key in allowed}
        if not values:
            return
        assignments = ", ".join(f"{key} = ?" for key in values)
        with sqlite3.connect(self.config.sqlite_path) as connection:
            connection.execute(
                f"UPDATE meetings SET {assignments} WHERE id = ?", (*values.values(), meeting_id)
            )
