from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lingualoop.core.domain import (
    LearningMaterial,
    PracticeSession,
    ReviewItem,
    ReviewStatus,
    SessionEvent,
)
from lingualoop.core.ports import EventStore


def default_database_path() -> Path:
    override = os.getenv("LINGUALOOP_DATA_DIR")
    if override:
        root = Path(override).expanduser()
    elif os.name == "nt":
        root = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData/Local")) / "LinguaLoop"
    elif os.name == "darwin":
        root = Path.home() / "Library/Application Support/LinguaLoop"
    else:
        root = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local/share")) / "LinguaLoop"
    root.mkdir(parents=True, exist_ok=True)
    return root / "lingualoop.sqlite3"


class SQLiteStore(EventStore):
    """Small JSON-payload SQLite store.

    Domain objects remain independent of sqlite3. The payload tables make the
    MVP easy to migrate while keeping events and queue records queryable.
    """

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path).expanduser() if path else default_database_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.path)
        self._connection.row_factory = sqlite3.Row
        self._initialize()

    def _initialize(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS schema_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS materials (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                material_id TEXT NOT NULL,
                status TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS review_items (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                due_at TEXT,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            INSERT OR IGNORE INTO schema_meta(key, value) VALUES ('version', '1');
            """
        )
        self._connection.commit()

    def close(self) -> None:
        self._connection.close()

    def save_material(self, material: LearningMaterial) -> None:
        payload = _dump(material)
        self._connection.execute(
            """
            INSERT INTO materials(id, created_at, payload) VALUES (?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET created_at=excluded.created_at, payload=excluded.payload
            """,
            (material.id, material.created_at.isoformat(), payload),
        )
        self._connection.commit()

    def list_materials(self, limit: int | None = None) -> list[LearningMaterial]:
        query = "SELECT payload FROM materials ORDER BY created_at DESC"
        params: tuple[Any, ...] = ()
        if limit is not None:
            query += " LIMIT ?"
            params = (limit,)
        rows = self._connection.execute(query, params).fetchall()
        return [LearningMaterial.model_validate(json.loads(row["payload"])) for row in rows]

    def get_material(self, material_id: str) -> LearningMaterial | None:
        row = self._connection.execute(
            "SELECT payload FROM materials WHERE id = ?", (material_id,)
        ).fetchone()
        return (
            LearningMaterial.model_validate(json.loads(row["payload"])) if row else None
        )

    def save_session(self, session: PracticeSession) -> None:
        payload = _dump(session)
        self._connection.execute(
            """
            INSERT INTO sessions(id, material_id, status, updated_at, payload)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET material_id=excluded.material_id,
              status=excluded.status, updated_at=excluded.updated_at, payload=excluded.payload
            """,
            (
                session.id,
                session.material_id,
                session.status.value,
                session.updated_at.isoformat(),
                payload,
            ),
        )
        for item in session.review_items:
            self.save_review_item(item, commit=False)
        self._connection.commit()

    def list_sessions(self, limit: int | None = None) -> list[PracticeSession]:
        query = "SELECT payload FROM sessions ORDER BY updated_at DESC"
        params: tuple[Any, ...] = ()
        if limit is not None:
            query += " LIMIT ?"
            params = (limit,)
        rows = self._connection.execute(query, params).fetchall()
        return [PracticeSession.model_validate(json.loads(row["payload"])) for row in rows]

    def get_session(self, session_id: str) -> PracticeSession | None:
        row = self._connection.execute(
            "SELECT payload FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        return PracticeSession.model_validate(json.loads(row["payload"])) if row else None

    def save_review_item(self, item: ReviewItem, *, commit: bool = True) -> None:
        self._connection.execute(
            """
            INSERT INTO review_items(id, status, due_at, payload) VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET status=excluded.status,
              due_at=excluded.due_at, payload=excluded.payload
            """,
            (item.id, item.status.value, _iso(item.due_at), _dump(item)),
        )
        if commit:
            self._connection.commit()

    def list_review_items(
        self, *, due_only: bool = False, limit: int | None = None
    ) -> list[ReviewItem]:
        now = datetime.now(timezone.utc).isoformat()
        query = "SELECT payload FROM review_items WHERE status = ?"
        params: list[Any] = [ReviewStatus.ACTIVE.value]
        if due_only:
            query += " AND (due_at IS NULL OR due_at <= ?)"
            params.append(now)
        query += " ORDER BY due_at ASC, id ASC"
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        rows = self._connection.execute(query, tuple(params)).fetchall()
        return [ReviewItem.model_validate(json.loads(row["payload"])) for row in rows]

    async def append(self, event: SessionEvent) -> None:
        self._connection.execute(
            "INSERT OR REPLACE INTO events(id, session_id, occurred_at, payload) VALUES (?, ?, ?, ?)",
            (event.id, event.session_id, event.occurred_at.isoformat(), _dump(event)),
        )
        self._connection.commit()

    async def append_many(self, events: list[SessionEvent]) -> None:
        for event in events:
            self._connection.execute(
                "INSERT OR REPLACE INTO events(id, session_id, occurred_at, payload) VALUES (?, ?, ?, ?)",
                (event.id, event.session_id, event.occurred_at.isoformat(), _dump(event)),
            )
        self._connection.commit()

    async def list_session_events(self, session_id: str) -> list[SessionEvent]:
        rows = self._connection.execute(
            "SELECT payload FROM events WHERE session_id = ? ORDER BY occurred_at ASC",
            (session_id,),
        ).fetchall()
        return [SessionEvent.model_validate(json.loads(row["payload"])) for row in rows]


def _dump(value: Any) -> str:
    return json.dumps(value.model_dump(mode="json"), ensure_ascii=False)


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None
