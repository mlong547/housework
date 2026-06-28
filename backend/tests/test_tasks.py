from typing import Any


def create_task(client: Any, **overrides: Any) -> dict[str, Any]:
    payload = {
        "title": "Replace HVAC filter",
        "description": "Use 20x25x1 filter from garage shelf.",
        "endGoalDate": "2026-07-01",
        "repeating": False,
    }
    payload.update(overrides)
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201
    return response.get_json()["data"]


def test_create_one_off_task(client):
    response = client.post(
        "/tasks",
        json={
            "title": "Replace HVAC filter",
            "description": "Use 20x25x1 filter from garage shelf.",
            "endGoalDate": "2026-07-01",
            "repeating": False,
        },
    )

    assert response.status_code == 201
    assert response.headers["Location"].startswith("/tasks/")
    body = response.get_json()
    task = body["data"]
    assert task["title"] == "Replace HVAC filter"
    assert task["status"] == "pending"
    assert task["endGoalDate"] == "2026-07-01"
    assert task["repeating"] is False
    assert task["recurrence"] is None
    assert task["completedAt"] is None
    assert task["createdAt"]
    assert task["updatedAt"]


def test_create_repeating_every_other_friday_task(client):
    response = client.post(
        "/tasks",
        json={
            "title": "Clean bathrooms",
            "endGoalDate": "2026-07-03",
            "repeating": True,
            "recurrence": {
                "frequency": "weekly",
                "interval": 2,
                "daysOfWeek": ["friday"],
                "startsOn": "2026-07-03",
            },
        },
    )

    assert response.status_code == 201
    task = response.get_json()["data"]
    assert task["repeating"] is True
    assert task["recurrence"] == {
        "frequency": "weekly",
        "interval": 2,
        "daysOfWeek": ["friday"],
        "startsOn": "2026-07-03",
    }


def test_create_rejects_repeating_task_without_recurrence(client):
    response = client.post(
        "/tasks",
        json={
            "title": "Clean bathrooms",
            "endGoalDate": "2026-07-03",
            "repeating": True,
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["details"]["field"] == "recurrence"


def test_create_rejects_recurrence_when_task_is_not_repeating(client):
    response = client.post(
        "/tasks",
        json={
            "title": "Clean bathrooms",
            "endGoalDate": "2026-07-03",
            "repeating": False,
            "recurrence": {
                "frequency": "weekly",
                "interval": 1,
                "daysOfWeek": ["friday"],
            },
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["details"]["field"] == "recurrence"


def test_create_rejects_end_goal_date_off_weekly_cadence(client):
    response = client.post(
        "/tasks",
        json={
            "title": "Clean bathrooms",
            "endGoalDate": "2026-07-10",
            "repeating": True,
            "recurrence": {
                "frequency": "weekly",
                "interval": 2,
                "daysOfWeek": ["friday"],
                "startsOn": "2026-07-03",
            },
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["details"]["field"] == "endGoalDate"


def test_create_rejects_boolean_interval(client):
    response = client.post(
        "/tasks",
        json={
            "title": "Clean bathrooms",
            "endGoalDate": "2026-07-03",
            "repeating": True,
            "recurrence": {
                "frequency": "weekly",
                "interval": True,
                "daysOfWeek": ["friday"],
            },
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["details"]["field"] == "recurrence.interval"


def test_create_accepts_monthly_day_of_month_task(client):
    response = client.post(
        "/tasks",
        json={
            "title": "Change water filter",
            "endGoalDate": "2026-08-15",
            "repeating": True,
            "recurrence": {
                "frequency": "monthly",
                "interval": 1,
                "dayOfMonth": 15,
                "startsOn": "2026-07-15",
            },
        },
    )

    assert response.status_code == 201
    assert response.get_json()["data"]["recurrence"]["dayOfMonth"] == 15


def test_list_tasks_filters_by_date_status_and_repeating(client):
    pending = create_task(client, title="Replace filter", endGoalDate="2026-07-01")
    completed = create_task(
        client,
        title="Clean fridge",
        endGoalDate="2026-07-03",
    )
    client.patch(
        f"/tasks/{completed['id']}",
        json={"status": "completed", "completedAt": "2026-07-03T20:25:00Z"},
    )
    create_task(
        client,
        title="Clean bathrooms",
        endGoalDate="2026-07-03",
        repeating=True,
        recurrence={
            "frequency": "weekly",
            "interval": 1,
            "daysOfWeek": ["friday"],
        },
    )

    date_response = client.get("/tasks?endGoalDate=2026-07-03")
    assert date_response.status_code == 200
    assert date_response.get_json()["meta"]["count"] == 2

    range_response = client.get("/tasks?endGoalDateFrom=2026-07-02&status=completed")
    assert range_response.status_code == 200
    assert [task["id"] for task in range_response.get_json()["data"]] == [
        completed["id"]
    ]

    repeating_response = client.get("/tasks?repeating=false")
    assert repeating_response.status_code == 200
    assert {task["id"] for task in repeating_response.get_json()["data"]} == {
        pending["id"],
        completed["id"],
    }


def test_get_task_by_id(client):
    created = create_task(client)

    response = client.get(f"/tasks/{created['id']}")

    assert response.status_code == 200
    assert response.get_json()["data"]["id"] == created["id"]


def test_get_task_returns_not_found(client):
    response = client.get("/tasks/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "not_found"


def test_put_replaces_task(client):
    created = create_task(client)

    response = client.put(
        f"/tasks/{created['id']}",
        json={
            "title": "Clean bathrooms",
            "description": None,
            "status": "pending",
            "endGoalDate": "2026-07-17",
            "repeating": True,
            "recurrence": {
                "frequency": "weekly",
                "interval": 2,
                "daysOfWeek": ["friday"],
                "startsOn": "2026-07-03",
            },
        },
    )

    assert response.status_code == 200
    task = response.get_json()["data"]
    assert task["title"] == "Clean bathrooms"
    assert task["description"] is None
    assert task["repeating"] is True
    assert task["recurrence"]["interval"] == 2


def test_put_requires_status(client):
    created = create_task(client)

    response = client.put(
        f"/tasks/{created['id']}",
        json={
            "title": "Clean bathrooms",
            "endGoalDate": "2026-07-17",
            "repeating": False,
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["details"]["field"] == "status"


def test_patch_updates_selected_fields(client):
    created = create_task(client)

    response = client.patch(
        f"/tasks/{created['id']}",
        json={"status": "completed", "completedAt": "2026-07-01T14:30:00Z"},
    )

    assert response.status_code == 200
    task = response.get_json()["data"]
    assert task["title"] == created["title"]
    assert task["status"] == "completed"
    assert task["completedAt"] == "2026-07-01T14:30:00Z"


def test_patch_to_pending_clears_completed_at(client):
    created = create_task(client)
    client.patch(
        f"/tasks/{created['id']}",
        json={"status": "completed", "completedAt": "2026-07-01T14:30:00Z"},
    )

    response = client.patch(f"/tasks/{created['id']}", json={"status": "pending"})

    assert response.status_code == 200
    task = response.get_json()["data"]
    assert task["status"] == "pending"
    assert task["completedAt"] is None


def test_patch_rejects_completed_at_without_time_component(client):
    created = create_task(client)

    response = client.patch(
        f"/tasks/{created['id']}",
        json={"status": "completed", "completedAt": "2026-07-01"},
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["details"]["field"] == "completedAt"


def test_patch_rejects_empty_body(client):
    created = create_task(client)

    response = client.patch(f"/tasks/{created['id']}", json={})

    assert response.status_code == 400


def test_delete_task(client):
    created = create_task(client)

    delete_response = client.delete(f"/tasks/{created['id']}")
    get_response = client.get(f"/tasks/{created['id']}")

    assert delete_response.status_code == 204
    assert delete_response.data == b""
    assert get_response.status_code == 404


def test_delete_task_returns_not_found(client):
    response = client.delete("/tasks/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404


def test_list_rejects_invalid_filters(client):
    response = client.get("/tasks?status=done")

    assert response.status_code == 400
    assert response.get_json()["error"]["details"]["field"] == "status"


def test_tasks_require_bearer_token(anonymous_client):
    response = anonymous_client.get("/tasks")

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "unauthorized"


def test_tasks_reject_invalid_bearer_token(anonymous_client):
    response = anonymous_client.get(
        "/tasks",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "unauthorized"


def test_tasks_are_isolated_by_authenticated_user(client, make_auth_client):
    created = create_task(client, title="User A task")
    other_client, _ = make_auth_client(
        google_sub="google-sub-2",
        email="other@example.com",
    )

    list_response = other_client.get("/tasks")
    get_response = other_client.get(f"/tasks/{created['id']}")
    patch_response = other_client.patch(
        f"/tasks/{created['id']}",
        json={"title": "Changed by user B"},
    )

    assert list_response.status_code == 200
    assert list_response.get_json() == {"data": [], "meta": {"count": 0}}
    assert get_response.status_code == 404
    assert patch_response.status_code == 404
