# Housework API

Flask API package for Housework.

## Development

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
flask --app housework_api run --debug
```

## Tests

```sh
pytest
```

## API

The Flask app implements the task API described in `../openapi/openapi.yaml`.
Tasks are stored in SQLite. Configure the database file with the Flask
`DATABASE` config value; by default the app uses `housework.sqlite3`.
