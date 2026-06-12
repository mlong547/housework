def test_get_task_returns_task_id(client):
    response = client.get("/task/abc-123")

    assert response.status_code == 200
    assert response.get_json() == {"id": "abc-123"}
