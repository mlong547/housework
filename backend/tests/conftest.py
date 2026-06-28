import pytest

from housework_api import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app()
    app.config.update(DATABASE=str(tmp_path / "test.sqlite3"), TESTING=True)

    return app.test_client()
