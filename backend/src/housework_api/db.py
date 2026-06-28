from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Optional

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
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


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        database = current_app.config["DATABASE"]
        if database != ":memory:":
            Path(database).parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(database)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA)
        g.db = connection
    return g.db


def close_db(_: Optional[BaseException] = None) -> None:
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_app(app: Any) -> None:
    app.teardown_appcontext(close_db)
