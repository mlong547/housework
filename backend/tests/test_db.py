import sqlite3

from housework_api import create_app
from housework_api.db import LEGACY_USER_ID, get_db


def test_legacy_tasks_are_backfilled_to_legacy_user(tmp_path):
    database = tmp_path / "legacy.sqlite3"
    connection = sqlite3.connect(database)
    connection.executescript(
        """
        CREATE TABLE tasks (
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
        INSERT INTO tasks (
            id, title, description, status, end_goal_date, repeating, recurrence,
            completed_at, created_at, updated_at
        ) VALUES (
            'legacy-task', 'Legacy task', NULL, 'pending', '2026-07-01', 0,
            NULL, NULL, '2026-06-27T00:00:00Z', '2026-06-27T00:00:00Z'
        );
        """
    )
    connection.close()

    app = create_app()
    app.config.update(DATABASE=str(database), TESTING=True)
    with app.app_context():
        db = get_db()
        task = db.execute("SELECT * FROM tasks WHERE id = 'legacy-task'").fetchone()
        legacy_user = db.execute(
            "SELECT * FROM users WHERE id = ?", (LEGACY_USER_ID,)
        ).fetchone()
        user_id_column = next(
            row
            for row in db.execute("PRAGMA table_info(tasks)").fetchall()
            if row["name"] == "user_id"
        )

    assert task["user_id"] == LEGACY_USER_ID
    assert legacy_user["email"] == "legacy-local-user@example.invalid"
    assert user_id_column["notnull"] == 1
