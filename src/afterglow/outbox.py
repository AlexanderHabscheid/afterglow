from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from .sms import CheckInMessage


def _iso_now() -> str:
    return datetime.now(UTC).isoformat()


class SQLiteSMSOutbox:
    def __init__(self, db_path: str | Path = "afterglow.db") -> None:
        self.db_path = str(db_path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    @contextmanager
    def _session(self):
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._session() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sms_outbox (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id TEXT NOT NULL,
                    recipient_id TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    body TEXT NOT NULL,
                    status TEXT NOT NULL,
                    provider_message_id TEXT,
                    provider_status TEXT,
                    created_at TEXT NOT NULL,
                    sent_at TEXT,
                    UNIQUE(match_id, recipient_id, channel)
                )
                """
            )
            self._ensure_column(connection, "provider_message_id", "TEXT")
            self._ensure_column(connection, "provider_status", "TEXT")

    def _ensure_column(self, connection: sqlite3.Connection, column_name: str, column_type: str) -> None:
        existing = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(sms_outbox)").fetchall()
        }
        if column_name not in existing:
            connection.execute(f"ALTER TABLE sms_outbox ADD COLUMN {column_name} {column_type}")

    def enqueue_messages(self, messages: list[CheckInMessage]) -> list[dict[str, object]]:
        queued_at = _iso_now()
        with self._session() as connection:
            for message in messages:
                connection.execute(
                    """
                    INSERT INTO sms_outbox (
                        match_id, recipient_id, channel, body, status, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(match_id, recipient_id, channel) DO UPDATE SET
                        body=excluded.body,
                        status=CASE
                            WHEN sms_outbox.status = 'sent' THEN sms_outbox.status
                            ELSE excluded.status
                        END
                    """,
                    (
                        message.match_id,
                        message.recipient_id,
                        message.channel,
                        message.body,
                        "queued",
                        queued_at,
                    ),
                )
        return self.list_messages(match_id=messages[0].match_id if messages else None)

    def list_messages(
        self,
        *,
        match_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, object]]:
        query = "SELECT * FROM sms_outbox"
        filters: list[str] = []
        values: list[object] = []

        if match_id is not None:
            filters.append("match_id = ?")
            values.append(match_id)
        if status is not None:
            filters.append("status = ?")
            values.append(status)
        if filters:
            query += " WHERE " + " AND ".join(filters)
        query += " ORDER BY id DESC LIMIT ?"
        values.append(limit)

        with self._session() as connection:
            rows = connection.execute(query, values).fetchall()
            return [dict(row) for row in rows]

    def mark_sent(
        self,
        message_id: int,
        *,
        provider_message_id: str | None = None,
        provider_status: str | None = None,
    ) -> dict[str, object]:
        with self._session() as connection:
            connection.execute(
                """
                UPDATE sms_outbox
                SET
                    status = 'sent',
                    sent_at = ?,
                    provider_message_id = COALESCE(?, provider_message_id),
                    provider_status = COALESCE(?, provider_status)
                WHERE id = ?
                """,
                (_iso_now(), provider_message_id, provider_status, message_id),
            )
            row = connection.execute(
                "SELECT * FROM sms_outbox WHERE id = ?",
                (message_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"Unknown outbox message id: {message_id}")
            return dict(row)
