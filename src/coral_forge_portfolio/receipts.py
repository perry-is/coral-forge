"""Append-only SQLite receipts containing workflow metadata, not source text."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any


class ReceiptStore:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with closing(self._connect()) as connection, connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS receipts (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )"""
            )

    def append(self, run_id: str, event_type: str, payload: dict[str, Any]) -> None:
        with closing(self._connect()) as connection, connection:
            connection.execute(
                "INSERT INTO receipts (run_id, event_type, payload_json) VALUES (?, ?, ?)",
                (run_id, event_type, json.dumps(payload, sort_keys=True)),
            )

    def list_for_run(self, run_id: str) -> list[dict[str, Any]]:
        with closing(self._connect()) as connection, connection:
            rows = connection.execute(
                "SELECT sequence, event_type, payload_json, created_at FROM receipts "
                "WHERE run_id = ? ORDER BY sequence",
                (run_id,),
            ).fetchall()
        return [
            {"sequence": seq, "event_type": event, "payload": json.loads(payload), "created_at": at}
            for seq, event, payload, at in rows
        ]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=FULL")
        return connection
