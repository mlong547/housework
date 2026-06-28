# Housework API

Flask API package for Housework.

## Development

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
flask --app housework_api run --debug
```

Configure Google login and signed app sessions with environment variables:

```sh
export GOOGLE_CLIENT_ID="your-google-oauth-client-id"
export APP_SECRET_KEY="a-long-random-secret"
export DATABASE="housework.sqlite3"
export SESSION_MAX_AGE_SECONDS="2592000"
```

## Tests

```sh
pytest
```

## API

The Flask app implements the task API described in `../openapi/openapi.yaml`.
Tasks are stored in SQLite. Configure the database file with the Flask
`DATABASE` config value; by default the app uses `housework.sqlite3`.

Clients sign in by sending a Google ID token to `POST /auth/google`:

```json
{
  "credential": "google-id-token-from-google"
}
```

The response includes an app session token and user profile. Send that token to
task endpoints as `Authorization: Bearer <token>`. Tasks are scoped to the
authenticated user.
