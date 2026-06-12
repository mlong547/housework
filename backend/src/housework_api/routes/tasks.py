from flask import Blueprint

tasks_bp = Blueprint("tasks", __name__)


@tasks_bp.get("/task/<task_id>")
def get_task(task_id: str) -> dict[str, str]:
    return {"id": task_id}
