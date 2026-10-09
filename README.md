# Railway Browser Automation Test

Minimal Python + Playwright test to verify Railway can run Python web services with headless Chromium.

## What This Tests

- Python 3.12 on Railway
- Flask web service bound to `PORT` env var
- Headless Chromium via Playwright
- Persistent background web service

## Files

| File              | Purpose                                        |
|-------------------|------------------------------------------------|
| `server.py`       | Flask app with `/health` and `/run-test`       |
| `requirements.txt`| Pinned dependencies (Playwright 1.49.1)        |
| `Dockerfile`      | Python 3.12 + Playwright Chromium build        |
| `.dockerignore`   | Excludes local artifacts from Docker build     |

## Endpoints

- `GET /health` — Returns `{"status": "ok", "service": "railway-browser-test"}`
- `GET /run-test` — Launches Chromium, navigates to example.com, returns title + HTTP status

## Deploy to Railway (CLI)

### 1. Login

```bash
railway login
```

### 2. Link to existing project

From this folder (`D:\test`):

```bash
railway link
```

Select your existing Railway project when prompted.

### 3. Deploy

```bash
railway up
```

Railway will build the Docker image and deploy. The build takes 2-5 minutes due to Chromium download.

### 4. Get the public URL

```bash
railway domain
```

### 5. Test

```bash
curl https://<your-app>.up.railway.app/health
curl https://<your-app>.up.railway.app/run-test
```

Expected `/run-test` response:

```json
{
  "success": true,
  "title": "Example Domain",
  "http_status": 200,
  "url": "https://example.com",
  "elapsed_seconds": 1.234,
  "peak_rss_mb": 150.2
}
```

## How the Dockerfile Works

1. Base: `python:3.12-slim`
2. Installs pinned Python deps from `requirements.txt`
3. Runs `playwright install --with-deps chromium` — downloads Chromium + OS libs during build
4. Serves via gunicorn on port 8080 (Railway injects `PORT` env var at runtime)

No database, Redis, or external services required.
