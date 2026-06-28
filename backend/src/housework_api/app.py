import os

from flask import Flask

from housework_api.auth import auth_bp
from housework_api.db import init_app
from housework_api.routes.tasks import tasks_bp


def read_session_max_age() -> int:
    raw_value = os.environ.get("SESSION_MAX_AGE_SECONDS", str(60 * 60 * 24 * 30))
    try:
        value = int(raw_value)
    except ValueError:
        return 60 * 60 * 24 * 30
    if value < 1:
        return 60 * 60 * 24 * 30
    return value


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        APP_SECRET_KEY=os.environ.get("APP_SECRET_KEY"),
        DATABASE=os.environ.get("DATABASE", "housework.sqlite3"),
        GOOGLE_CLIENT_ID=os.environ.get("GOOGLE_CLIENT_ID"),
        SESSION_MAX_AGE_SECONDS=read_session_max_age(),
    )
    init_app(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)
    return app
