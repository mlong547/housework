from flask import Flask

from housework_api.db import init_app
from housework_api.routes.tasks import tasks_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(DATABASE="housework.sqlite3")
    init_app(app)
    app.register_blueprint(tasks_bp)
    return app
