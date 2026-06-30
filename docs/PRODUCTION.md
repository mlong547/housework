# Production Deployment

This deployment path targets a Windows desktop running Docker Desktop with the
WSL2 backend.

## Shape

```text
browser or phone
  -> Caddy container
    -> serves the built React frontend
    -> proxies /auth/* and /tasks* to the Flask backend

backend container
  -> Gunicorn
  -> Flask app
  -> SQLite database on a persistent Docker volume
```

## Prerequisites

- Docker Desktop is installed and running.
- Docker Desktop uses Linux containers.
- Docker Desktop is configured to start when you sign in.
- The desktop is allowed to stay awake while hosting the app.
- Google OAuth is configured for the final app origin.

Verify Docker from PowerShell 7:

```powershell
docker version
docker compose version
```

## First Run

Copy the environment template:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and set:

- `APP_SECRET_KEY`
- `GOOGLE_CLIENT_ID`
- `HOUSEWORK_HTTP_PORT`

Generate a strong app secret:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Build and start the app:

```powershell
docker compose up --build -d
```

Open the app:

```text
http://localhost:8080/
```

If another device on your LAN should access it, allow inbound Windows Firewall
traffic for the chosen `HOUSEWORK_HTTP_PORT`.

## Operations

View status:

```powershell
docker compose ps
```

View logs:

```powershell
docker compose logs -f
```

Stop:

```powershell
docker compose down
```

Update after pulling new code:

```powershell
docker compose up --build -d
```

## Data

SQLite data lives in the named Docker volume `housework-data`.

Back up the volume regularly. A simple first pass is to stop the backend
container, copy the database out of it, and start the stack again:

```powershell
docker compose stop backend
docker compose cp backend:/data/housework.sqlite3 .\housework.sqlite3.backup
docker compose up -d
```

For a more reliable production setup, automate a scheduled backup to a location
outside the repository.

## Release Artifacts

The manual `Production Artifacts` GitHub Actions workflow builds:

- frontend static files
- backend Python wheel
- backend Docker image archive
- web/proxy Docker image archive
- Docker deployment bundle

It zips each artifact and uploads them to a draft GitHub release.

To run from release artifacts instead of building locally:

1. Download and unzip `housework-docker-deploy.zip`.
2. Download and unzip `housework-backend-image.zip`.
3. Download and unzip `housework-web-image.zip`.
4. Load the images:

```powershell
docker load --input .\housework-backend-image.tar
docker load --input .\housework-web-image.tar
```

5. Copy `.env.example` to `.env`, edit the values, then start without building:

```powershell
docker compose up -d --no-build
```
