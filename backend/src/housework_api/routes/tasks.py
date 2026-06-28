from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timezone
from typing import Any, Optional, Union

from flask import Blueprint, Response, jsonify, request, url_for

from housework_api.auth import current_user_id, require_auth
from housework_api.db import get_db
from housework_api.tasks_repository import (
    delete_task_for_user,
    fetch_task_for_user,
    insert_task_for_user,
    list_tasks_for_user,
    replace_task_for_user,
    update_task_for_user,
)

tasks_bp = Blueprint("tasks", __name__)

STATUSES = {"pending", "completed"}
FREQUENCIES = {"daily", "weekly", "monthly", "yearly"}
DAYS_OF_WEEK = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}
CREATE_FIELDS = {"title", "description", "endGoalDate", "repeating", "recurrence"}
UPDATE_FIELDS = CREATE_FIELDS | {"status", "completedAt"}
ErrorResult = tuple[Response, int]
DateOrError = Union[date, ErrorResult]


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def error_response(
    status_code: int, code: str, message: str, details: Optional[dict[str, Any]] = None
) -> ErrorResult:
    body: dict[str, Any] = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return jsonify(body), status_code


def validation_error(message: str, field: Optional[str] = None) -> ErrorResult:
    details = {"field": field} if field else None
    return error_response(400, "validation_error", message, details)


def not_found() -> ErrorResult:
    return error_response(404, "not_found", "Task not found.")


def parse_date(value: Any, field: str) -> DateOrError:
    if not isinstance(value, str):
        return validation_error(f"{field} must be an ISO 8601 date.", field)
    try:
        return date.fromisoformat(value)
    except ValueError:
        return validation_error(f"{field} must be an ISO 8601 date.", field)


def validate_datetime(value: Any, field: str) -> Optional[ErrorResult]:
    if value is None:
        return None
    if not isinstance(value, str):
        return validation_error(f"{field} must be an ISO 8601 date-time.", field)
    if "T" not in value:
        return validation_error(f"{field} must be an ISO 8601 date-time.", field)
    normalized = value.replace("Z", "+00:00")
    try:
        datetime.fromisoformat(normalized)
    except ValueError:
        return validation_error(f"{field} must be an ISO 8601 date-time.", field)
    return None


def validate_recurrence(
    recurrence: Any, end_goal_date: date
) -> Union[tuple[dict[str, Any], None], tuple[None, ErrorResult]]:
    if not isinstance(recurrence, dict):
        return None, validation_error(
            "recurrence is required when repeating is true.", "recurrence"
        )

    frequency = recurrence.get("frequency")
    interval = recurrence.get("interval")
    if frequency not in FREQUENCIES:
        return None, validation_error(
            "recurrence.frequency must be daily, weekly, monthly, or yearly.",
            "recurrence.frequency",
        )
    if type(interval) is not int or interval < 1:
        return None, validation_error(
            "recurrence.interval must be an integer greater than 0.",
            "recurrence.interval",
        )

    cleaned: dict[str, Any] = {"frequency": frequency, "interval": interval}
    starts_on_value = recurrence.get("startsOn")
    if starts_on_value is not None:
        starts_on = parse_date(starts_on_value, "recurrence.startsOn")
        if not isinstance(starts_on, date):
            return None, starts_on
        cleaned["startsOn"] = starts_on_value
    else:
        starts_on = end_goal_date

    ends_on_value = recurrence.get("endsOn")
    if ends_on_value is not None:
        ends_on = parse_date(ends_on_value, "recurrence.endsOn")
        if not isinstance(ends_on, date):
            return None, ends_on
        if end_goal_date > ends_on:
            return None, validation_error(
                "endGoalDate must be on or before recurrence.endsOn.",
                "endGoalDate",
            )
        cleaned["endsOn"] = ends_on_value

    if end_goal_date < starts_on:
        return None, validation_error(
            "endGoalDate must be on or after recurrence.startsOn.", "endGoalDate"
        )

    if frequency == "daily":
        days_between = (end_goal_date - starts_on).days
        if days_between % interval != 0:
            return None, cadence_error()

    if frequency == "weekly":
        days = recurrence.get("daysOfWeek")
        if not isinstance(days, list) or not days:
            return None, validation_error(
                "recurrence.daysOfWeek is required for weekly tasks.",
                "recurrence.daysOfWeek",
            )
        if len(set(days)) != len(days) or any(day not in DAYS_OF_WEEK for day in days):
            return None, validation_error(
                "recurrence.daysOfWeek must contain unique lowercase weekday names.",
                "recurrence.daysOfWeek",
            )
        if end_goal_date.weekday() not in {DAYS_OF_WEEK[day] for day in days}:
            return None, cadence_error()
        weeks_between = (end_goal_date - starts_on).days // 7
        if weeks_between % interval != 0:
            return None, cadence_error()
        cleaned["daysOfWeek"] = days

    if frequency == "monthly":
        day_of_month = recurrence.get("dayOfMonth")
        week_of_month = recurrence.get("weekOfMonth")
        days = recurrence.get("daysOfWeek")
        if day_of_month is not None:
            if type(day_of_month) is not int or not 1 <= day_of_month <= 31:
                return None, validation_error(
                    "recurrence.dayOfMonth must be between 1 and 31.",
                    "recurrence.dayOfMonth",
                )
            if end_goal_date.day != day_of_month:
                return None, cadence_error()
            cleaned["dayOfMonth"] = day_of_month
        elif week_of_month is not None or days is not None:
            if type(week_of_month) is not int or not 1 <= week_of_month <= 5:
                return None, validation_error(
                    "recurrence.weekOfMonth must be between 1 and 5.",
                    "recurrence.weekOfMonth",
                )
            if (
                not isinstance(days, list)
                or len(days) != 1
                or days[0] not in DAYS_OF_WEEK
            ):
                return None, validation_error(
                    "monthly weekOfMonth rules require one valid day in daysOfWeek.",
                    "recurrence.daysOfWeek",
                )
            if end_goal_date.weekday() != DAYS_OF_WEEK[days[0]]:
                return None, cadence_error()
            if ((end_goal_date.day - 1) // 7) + 1 != week_of_month:
                return None, cadence_error()
            cleaned["weekOfMonth"] = week_of_month
            cleaned["daysOfWeek"] = days
        else:
            return None, validation_error(
                "recurrence.dayOfMonth or recurrence.weekOfMonth is required "
                "for monthly tasks.",
                "recurrence",
            )
        months_between = (
            (end_goal_date.year - starts_on.year) * 12
            + end_goal_date.month
            - starts_on.month
        )
        if months_between % interval != 0:
            return None, cadence_error()

    if frequency == "yearly":
        month = recurrence.get("monthOfYear")
        day = recurrence.get("dayOfMonth")
        if type(month) is not int or not 1 <= month <= 12:
            return None, validation_error(
                "recurrence.monthOfYear must be between 1 and 12.",
                "recurrence.monthOfYear",
            )
        if type(day) is not int or not 1 <= day <= 31:
            return None, validation_error(
                "recurrence.dayOfMonth must be between 1 and 31.",
                "recurrence.dayOfMonth",
            )
        if end_goal_date.month != month or end_goal_date.day != day:
            return None, cadence_error()
        years_between = end_goal_date.year - starts_on.year
        if years_between % interval != 0:
            return None, cadence_error()
        cleaned["monthOfYear"] = month
        cleaned["dayOfMonth"] = day

    return cleaned, None


def cadence_error() -> ErrorResult:
    return validation_error(
        "endGoalDate must fall on the recurrence cadence.", "endGoalDate"
    )


def validate_payload(
    payload: Any, *, partial: bool = False, replacement: bool = False
) -> Union[tuple[dict[str, Any], None], tuple[None, ErrorResult]]:
    if not isinstance(payload, dict):
        return None, validation_error("Request body must be a JSON object.")
    if partial and not payload:
        return None, validation_error("Request body must include at least one field.")

    allowed = UPDATE_FIELDS if partial or replacement else CREATE_FIELDS
    unknown = sorted(set(payload) - allowed)
    if unknown:
        return None, validation_error(f"Unknown field: {unknown[0]}.", unknown[0])

    cleaned: dict[str, Any] = {}
    if "title" in payload:
        title = payload["title"]
        if not isinstance(title, str) or not title.strip() or len(title) > 120:
            return None, validation_error(
                "title must be a non-empty string up to 120 characters.", "title"
            )
        cleaned["title"] = title
    elif not partial:
        return None, validation_error("title is required.", "title")

    if "description" in payload:
        description = payload["description"]
        if description is not None and (
            not isinstance(description, str) or len(description) > 2000
        ):
            return None, validation_error(
                "description must be null or a string up to 2000 characters.",
                "description",
            )
        cleaned["description"] = description

    if "status" in payload:
        if payload["status"] not in STATUSES:
            return None, validation_error(
                "status must be pending or completed.", "status"
            )
        cleaned["status"] = payload["status"]
    elif replacement:
        return None, validation_error("status is required.", "status")
    elif not partial:
        cleaned["status"] = "pending"

    if "endGoalDate" in payload:
        end_goal_date = parse_date(payload["endGoalDate"], "endGoalDate")
        if not isinstance(end_goal_date, date):
            return None, end_goal_date
        cleaned["endGoalDate"] = payload["endGoalDate"]
    elif not partial:
        return None, validation_error("endGoalDate is required.", "endGoalDate")

    if "repeating" in payload:
        if not isinstance(payload["repeating"], bool):
            return None, validation_error("repeating must be a boolean.", "repeating")
        cleaned["repeating"] = payload["repeating"]
    elif not partial:
        return None, validation_error("repeating is required.", "repeating")

    if "completedAt" in payload:
        error = validate_datetime(payload["completedAt"], "completedAt")
        if error:
            return None, error
        cleaned["completedAt"] = payload["completedAt"]

    if "recurrence" in payload:
        cleaned["recurrence"] = payload["recurrence"]

    return cleaned, None


def validate_task_state(
    state: dict[str, Any],
) -> Union[tuple[dict[str, Any], None], tuple[None, ErrorResult]]:
    repeating = state.get("repeating")
    recurrence = state.get("recurrence")

    if repeating:
        end_goal_date = parse_date(state.get("endGoalDate"), "endGoalDate")
        if not isinstance(end_goal_date, date):
            return None, end_goal_date
        recurrence, error = validate_recurrence(recurrence, end_goal_date)
        if error:
            return None, error
        state["recurrence"] = recurrence
    elif recurrence not in (None, {}):
        return None, validation_error(
            "recurrence must be omitted or null when repeating is false.", "recurrence"
        )
    else:
        state["recurrence"] = None

    if state.get("status") == "pending":
        state["completedAt"] = None

    return state, None


def row_to_task(row: Any) -> dict[str, Any]:
    recurrence = json.loads(row["recurrence"]) if row["recurrence"] else None
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "status": row["status"],
        "endGoalDate": row["end_goal_date"],
        "repeating": bool(row["repeating"]),
        "recurrence": recurrence,
        "completedAt": row["completed_at"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def fetch_task(task_id: str) -> Any:
    return fetch_task_for_user(current_user_id(), task_id)


@tasks_bp.get("/tasks")
@require_auth
def list_tasks() -> ErrorResult:
    filters: dict[str, Any] = {}

    for name in ("endGoalDate", "endGoalDateFrom", "endGoalDateTo"):
        value = request.args.get(name)
        if value is not None:
            parsed = parse_date(value, name)
            if not isinstance(parsed, date):
                return parsed
            filters[name] = value

    end_goal_date = request.args.get("endGoalDate")
    if end_goal_date:
        filters["endGoalDate"] = end_goal_date

    end_goal_date_from = request.args.get("endGoalDateFrom")
    if end_goal_date_from:
        filters["endGoalDateFrom"] = end_goal_date_from

    end_goal_date_to = request.args.get("endGoalDateTo")
    if end_goal_date_to:
        filters["endGoalDateTo"] = end_goal_date_to

    status = request.args.get("status")
    if status is not None:
        if status not in STATUSES:
            return validation_error("status must be pending or completed.", "status")
        filters["status"] = status

    repeating = request.args.get("repeating")
    if repeating is not None:
        if repeating not in {"true", "false"}:
            return validation_error("repeating must be true or false.", "repeating")
        filters["repeating"] = repeating == "true"

    rows = list_tasks_for_user(current_user_id(), filters)
    tasks = [row_to_task(row) for row in rows]
    return jsonify({"data": tasks, "meta": {"count": len(tasks)}}), 200


@tasks_bp.post("/tasks")
@require_auth
def create_task() -> ErrorResult:
    payload, error = validate_payload(request.get_json(silent=True), partial=False)
    if error:
        return error
    assert payload is not None

    state, error = validate_task_state(payload)
    if error:
        return error
    assert state is not None

    task_id = str(uuid.uuid4())
    now = utc_now()
    insert_task_for_user(current_user_id(), task_id, state, now)
    get_db().commit()

    task = row_to_task(fetch_task(task_id))
    response = jsonify({"data": task})
    response.headers["Location"] = url_for("tasks.get_task", task_id=task_id)
    return response, 201


@tasks_bp.get("/tasks/<task_id>")
@require_auth
def get_task(task_id: str) -> ErrorResult:
    row = fetch_task(task_id)
    if row is None:
        return not_found()
    return jsonify({"data": row_to_task(row)}), 200


@tasks_bp.put("/tasks/<task_id>")
@require_auth
def replace_task(task_id: str) -> ErrorResult:
    if fetch_task(task_id) is None:
        return not_found()

    payload, error = validate_payload(
        request.get_json(silent=True), partial=False, replacement=True
    )
    if error:
        return error
    assert payload is not None

    state, error = validate_task_state(payload)
    if error:
        return error
    assert state is not None

    now = utc_now()
    replace_task_for_user(current_user_id(), task_id, state, now)
    get_db().commit()
    return jsonify({"data": row_to_task(fetch_task(task_id))}), 200


@tasks_bp.patch("/tasks/<task_id>")
@require_auth
def update_task(task_id: str) -> ErrorResult:
    row = fetch_task(task_id)
    if row is None:
        return not_found()

    payload, error = validate_payload(request.get_json(silent=True), partial=True)
    if error:
        return error
    assert payload is not None

    state = row_to_task(row)
    state.update(payload)
    state, error = validate_task_state(state)
    if error:
        return error
    assert state is not None

    now = utc_now()
    update_task_for_user(current_user_id(), task_id, state, now)
    get_db().commit()
    return jsonify({"data": row_to_task(fetch_task(task_id))}), 200


@tasks_bp.delete("/tasks/<task_id>")
@require_auth
def delete_task(task_id: str) -> Union[ErrorResult, Response]:
    if fetch_task(task_id) is None:
        return not_found()
    delete_task_for_user(current_user_id(), task_id)
    get_db().commit()
    return Response(status=204)
