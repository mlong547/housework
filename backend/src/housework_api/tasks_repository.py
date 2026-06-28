from __future__ import annotations

import json
from typing import Any, Optional

from housework_api.db import get_db


def serialize_recurrence(recurrence: Any) -> Optional[str]:
    return json.dumps(recurrence) if recurrence else None


def list_tasks_for_user(user_id: str, filters: dict[str, Any]) -> list[Any]:
    predicates = ["user_id = ?"]
    values: list[Any] = [user_id]

    if filters.get("endGoalDate"):
        predicates.append("end_goal_date = ?")
        values.append(filters["endGoalDate"])
    if filters.get("endGoalDateFrom"):
        predicates.append("end_goal_date >= ?")
        values.append(filters["endGoalDateFrom"])
    if filters.get("endGoalDateTo"):
        predicates.append("end_goal_date <= ?")
        values.append(filters["endGoalDateTo"])
    if filters.get("status"):
        predicates.append("status = ?")
        values.append(filters["status"])
    if "repeating" in filters:
        predicates.append("repeating = ?")
        values.append(1 if filters["repeating"] else 0)

    query = "SELECT * FROM tasks WHERE " + " AND ".join(predicates)
    query += " ORDER BY end_goal_date, created_at"
    return list(get_db().execute(query, values).fetchall())


def fetch_task_for_user(user_id: str, task_id: str) -> Any:
    return (
        get_db()
        .execute(
            "SELECT * FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, user_id),
        )
        .fetchone()
    )


def insert_task_for_user(
    user_id: str, task_id: str, state: dict[str, Any], now: str
) -> None:
    get_db().execute(
        """
        INSERT INTO tasks (
            id, user_id, title, description, status, end_goal_date, repeating,
            recurrence, completed_at, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            task_id,
            user_id,
            state["title"],
            state.get("description"),
            state["status"],
            state["endGoalDate"],
            int(state["repeating"]),
            serialize_recurrence(state["recurrence"]),
            state.get("completedAt"),
            now,
            now,
        ),
    )


def replace_task_for_user(
    user_id: str, task_id: str, state: dict[str, Any], now: str
) -> None:
    get_db().execute(
        """
        UPDATE tasks
           SET title = ?, description = ?, status = ?, end_goal_date = ?,
               repeating = ?, recurrence = ?, completed_at = ?, updated_at = ?
         WHERE id = ?
           AND user_id = ?
        """,
        (
            state["title"],
            state.get("description"),
            state["status"],
            state["endGoalDate"],
            int(state["repeating"]),
            serialize_recurrence(state["recurrence"]),
            state.get("completedAt"),
            now,
            task_id,
            user_id,
        ),
    )


def update_task_for_user(
    user_id: str, task_id: str, state: dict[str, Any], now: str
) -> None:
    replace_task_for_user(user_id, task_id, state, now)


def delete_task_for_user(user_id: str, task_id: str) -> None:
    get_db().execute(
        "DELETE FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, user_id),
    )
