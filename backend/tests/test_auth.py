import pytest

from housework_api import create_app
from housework_api.db import get_db


def test_google_auth_requests_transport_is_installed():
    from google.auth.transport import requests

    assert requests.Request


def test_invalid_session_max_age_env_falls_back(monkeypatch):
    monkeypatch.setenv("SESSION_MAX_AGE_SECONDS", "not-an-int")

    app = create_app()

    assert app.config["SESSION_MAX_AGE_SECONDS"] == 60 * 60 * 24 * 30


def test_non_positive_session_max_age_env_falls_back(monkeypatch):
    monkeypatch.setenv("SESSION_MAX_AGE_SECONDS", "0")

    app = create_app()

    assert app.config["SESSION_MAX_AGE_SECONDS"] == 60 * 60 * 24 * 30


def test_google_login_success_creates_user_and_returns_token(
    anonymous_client, app, monkeypatch
):
    seen = {}

    def fake_verify_google_id_token(token, client_id):
        seen["token"] = token
        seen["client_id"] = client_id
        return {
            "sub": "google-sub-123",
            "email": "person@example.com",
            "email_verified": True,
            "name": "Person Example",
            "picture": "https://example.com/person.png",
        }

    monkeypatch.setattr(
        "housework_api.auth.verify_google_id_token",
        fake_verify_google_id_token,
    )

    response = anonymous_client.post(
        "/auth/google",
        json={"credential": "google-id-token"},
    )

    assert response.status_code == 200
    body = response.get_json()["data"]
    assert body["token"]
    assert body["user"]["email"] == "person@example.com"
    assert seen == {
        "token": "google-id-token",
        "client_id": "test-client-id.apps.googleusercontent.com",
    }
    with app.app_context():
        row = (
            get_db()
            .execute(
                "SELECT * FROM users WHERE google_sub = ?",
                ("google-sub-123",),
            )
            .fetchone()
        )
    assert row["email"] == "person@example.com"


def test_google_login_rejects_invalid_token(anonymous_client, monkeypatch):
    def fake_verify_google_id_token(token, client_id):
        raise ValueError("invalid token")

    monkeypatch.setattr(
        "housework_api.auth.verify_google_id_token",
        fake_verify_google_id_token,
    )

    response = anonymous_client.post(
        "/auth/google",
        json={"credential": "bad-token"},
    )

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "invalid_google_token"


def test_google_login_rejects_unverified_email(anonymous_client, monkeypatch):
    def fake_verify_google_id_token(token, client_id):
        return {
            "sub": "google-sub-123",
            "email": "person@example.com",
            "email_verified": False,
        }

    monkeypatch.setattr(
        "housework_api.auth.verify_google_id_token",
        fake_verify_google_id_token,
    )

    response = anonymous_client.post(
        "/auth/google",
        json={"credential": "google-id-token"},
    )

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "invalid_google_token"


@pytest.mark.parametrize(
    ("key", "message"),
    [
        ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_ID is not configured."),
        ("APP_SECRET_KEY", "APP_SECRET_KEY is not configured."),
    ],
)
def test_google_login_requires_config(anonymous_client, app, key, message):
    app.config[key] = None

    response = anonymous_client.post(
        "/auth/google",
        json={"credential": "google-id-token"},
    )

    assert response.status_code == 500
    assert response.get_json()["error"] == {
        "code": "config_error",
        "message": message,
    }


def test_google_login_requires_credential(anonymous_client):
    response = anonymous_client.post("/auth/google", json={})

    assert response.status_code == 400
    assert response.get_json()["error"]["details"]["field"] == "credential"
