from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Optional

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    google_sub TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL,
    name TEXT,
    picture TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL CHECK (status IN ('pending', 'completed')),
    end_goal_date TEXT NOT NULL,
    repeating INTEGER NOT NULL CHECK (repeating IN (0, 1)),
    recurrence TEXT,
    completed_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

LEGACY_USER_ID = "legacy-local-user"


def table_columns(connection: sqlite3.Connection, table: str) -> dict[str, Any]:
    return {
        row["name"]: row
        for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
    }


def seed_legacy_user(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        INSERT OR IGNORE INTO users (
            id, google_sub, email, name, picture, created_at, updated_at
        ) VALUES (
            ?, ?, ?, ?, NULL,
            strftime('%Y-%m-%dT%H:%M:%SZ', 'now'),
            strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
        )
        """,
        (
            LEGACY_USER_ID,
            LEGACY_USER_ID,
            "legacy-local-user@example.invalid",
            "Legacy Local User",
        ),
    )


def migrate_tasks_for_auth(connection: sqlite3.Connection) -> None:
    columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(tasks)").fetchall()
    }
    if not columns:
        return

    has_user_id = "user_id" in columns
    user_id_column = table_columns(connection, "tasks").get("user_id")
    user_id_required = bool(user_id_column and user_id_column["notnull"])
    orphaned_tasks = 0
    if has_user_id:
        orphaned_tasks = connection.execute(
            "SELECT COUNT(*) AS count FROM tasks WHERE user_id IS NULL"
        ).fetchone()["count"]

    if has_user_id and user_id_required and orphaned_tasks == 0:
        return

    seed_legacy_user(connection)
    connection.execute("ALTER TABLE tasks RENAME TO tasks_legacy")
    connection.executescript(
        """
        CREATE TABLE tasks (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL CHECK (status IN ('pending', 'completed')),
            end_goal_date TEXT NOT NULL,
            repeating INTEGER NOT NULL CHECK (repeating IN (0, 1)),
            recurrence TEXT,
            completed_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """
    )
    user_id_expression = (
        "COALESCE(user_id, ?)" if has_user_id else "?"
    )
    connection.execute(
        f"""
        INSERT INTO tasks (
            id, user_id, title, description, status, end_goal_date, repeating,
            recurrence, completed_at, created_at, updated_at
        )
        SELECT
            id, {user_id_expression}, title, description, status, end_goal_date,
            repeating, recurrence, completed_at, created_at, updated_at
        FROM tasks_legacy
        """,
        (LEGACY_USER_ID,),
    )
    connection.execute("DROP TABLE tasks_legacy")


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        database = current_app.config["DATABASE"]
        if database != ":memory:":
            Path(database).parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(database)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA)
        migrate_tasks_for_auth(connection)
        connection.commit()
        g.db = connection
    return g.db


def close_db(_: Optional[BaseException] = None) -> None:
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_app(app: Any) -> None:
    app.teardown_appcontext(close_db)
