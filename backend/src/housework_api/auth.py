from __future__ import annotations

import uuid
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, cast

from flask import Blueprint, Response, current_app, g, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from housework_api.db import get_db

auth_bp = Blueprint("auth", __name__)

F = TypeVar("F", bound=Callable[..., Any])
ErrorResult = tuple[Response, int]


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


def app_secret_key() -> Optional[str]:
    return current_app.config.get("APP_SECRET_KEY")


def google_client_id() -> Optional[str]:
    return current_app.config.get("GOOGLE_CLIENT_ID")


def session_serializer() -> URLSafeTimedSerializer:
    secret_key = app_secret_key()
    if not secret_key:
        raise RuntimeError("APP_SECRET_KEY is not configured.")
    return URLSafeTimedSerializer(secret_key, salt="housework-session")


def create_session_token(user_id: str) -> str:
    return session_serializer().dumps({"user_id": user_id})


def verify_session_token(token: str) -> Optional[str]:
    try:
        payload = session_serializer().loads(
            token,
            max_age=current_app.config["SESSION_MAX_AGE_SECONDS"],
        )
    except (BadSignature, RuntimeError, SignatureExpired):
        return None
    if not isinstance(payload, dict) or not isinstance(payload.get("user_id"), str):
        return None
    return payload["user_id"]


def verify_google_id_token(token: str, client_id: str) -> dict[str, Any]:
    from google.auth.exceptions import GoogleAuthError
    from google.auth.transport import requests as google_requests
    from google.auth.transport.requests import TransportError
    from google.oauth2 import id_token

    try:
        return id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            client_id,
        )
    except (GoogleAuthError, TransportError) as exc:
        raise ValueError(str(exc)) from exc


def row_to_user(row: Any) -> dict[str, Any]:
    return {
        "id": row["id"],
        "email": row["email"],
        "name": row["name"],
        "picture": row["picture"],
    }


def upsert_google_user(claims: dict[str, Any]) -> dict[str, Any]:
    google_sub = claims.get("sub")
    email = claims.get("email")
    if not isinstance(google_sub, str) or not google_sub:
        raise ValueError("Google token is missing subject.")
    if not isinstance(email, str) or not email:
        raise ValueError("Google token is missing email.")
    if claims.get("email_verified") is not True:
        raise ValueError("Google email is not verified.")

    name = claims.get("name")
    picture = claims.get("picture")
    if name is not None and not isinstance(name, str):
        name = None
    if picture is not None and not isinstance(picture, str):
        picture = None

    db = get_db()
    now = utc_now()
    row = db.execute(
        "SELECT * FROM users WHERE google_sub = ?",
        (google_sub,),
    ).fetchone()
    if row is None:
        user_id = str(uuid.uuid4())
        db.execute(
            """
            INSERT INTO users (
                id, google_sub, email, name, picture, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, google_sub, email, name, picture, now, now),
        )
    else:
        user_id = row["id"]
        db.execute(
            """
            UPDATE users
               SET email = ?, name = ?, picture = ?, updated_at = ?
             WHERE id = ?
            """,
            (email, name, picture, now, user_id),
        )
    db.commit()
    return row_to_user(
        db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    )


@auth_bp.post("/auth/google")
def google_login() -> ErrorResult:
    client_id = google_client_id()
    if not client_id:
        return error_response(
            500,
            "config_error",
            "GOOGLE_CLIENT_ID is not configured.",
        )
    if not app_secret_key():
        return error_response(
            500,
            "config_error",
            "APP_SECRET_KEY is not configured.",
        )

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response(
            400, "validation_error", "Request body must be a JSON object."
        )
    credential = payload.get("credential", payload.get("idToken"))
    if not isinstance(credential, str) or not credential:
        return error_response(
            400,
            "validation_error",
            "credential is required.",
            {"field": "credential"},
        )

    try:
        claims = verify_google_id_token(credential, client_id)
        user = upsert_google_user(claims)
    except ValueError as exc:
        return error_response(401, "invalid_google_token", str(exc))

    return jsonify(
        {"data": {"token": create_session_token(user["id"]), "user": user}}
    ), 200


def require_auth(view: F) -> F:
    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        if not app_secret_key():
            return error_response(
                500,
                "config_error",
                "APP_SECRET_KEY is not configured.",
            )

        auth_header = request.headers.get("Authorization", "")
        scheme, _, token = auth_header.partition(" ")
        if scheme.lower() != "bearer" or not token:
            return error_response(401, "unauthorized", "Bearer token is required.")

        user_id = verify_session_token(token)
        if user_id is None:
            return error_response(401, "unauthorized", "Bearer token is invalid.")

        user = (
            get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        )
        if user is None:
            return error_response(401, "unauthorized", "Bearer token is invalid.")

        g.current_user = user
        return view(*args, **kwargs)

    return cast(F, wrapped)
