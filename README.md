# Housework

Housework is starting as a Flask API with room for a future React frontend in the same repository.

## Repository layout

```text
backend/         Flask API package, tests, and Python build metadata
```

## Backend

Create a virtual environment and install the backend package in editable mode:

```sh
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Run the API locally:

```sh
flask --app housework_api run --debug
```

Run the tests:

```sh
pytest
```

The current API surface is:

- `GET /task/<id>` returns `{"id": "<id>"}`
