import pytest

from housework_api import create_app
from housework_api.auth import create_session_token, utc_now
from housework_api.db import get_db


@pytest.fixture
def app(tmp_path):
    app = create_app()
    app.config.update(
        APP_SECRET_KEY="test-secret",
        DATABASE=str(tmp_path / "test.sqlite3"),
        GOOGLE_CLIENT_ID="test-client-id.apps.googleusercontent.com",
        TESTING=True,
    )

    return app


@pytest.fixture
def make_user(app):
    def _make_user(
        *,
        google_sub: str = "google-sub-1",
        email: str = "user@example.com",
        name: str = "Test User",
        picture: str = "https://example.com/avatar.png",
    ):
        with app.app_context():
            now = utc_now()
            user_id = google_sub
            get_db().execute(
                """
                INSERT INTO users (
                    id, google_sub, email, name, picture, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, google_sub, email, name, picture, now, now),
            )
            get_db().commit()
            return {
                "id": user_id,
                "email": email,
                "name": name,
                "picture": picture,
            }

    return _make_user


@pytest.fixture
def make_auth_client(app, make_user):
    def _make_auth_client(**user_overrides):
        user = make_user(**user_overrides)
        client = app.test_client()
        with app.app_context():
            token = create_session_token(user["id"])
        client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {token}"
        return client, user

    return _make_auth_client


@pytest.fixture
def client(make_auth_client):
    return make_auth_client()[0]


@pytest.fixture
def anonymous_client(app):
    return app.test_client()
