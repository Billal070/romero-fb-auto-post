# Botkeep Hosting Test

Minimal Python test project to verify Python + Playwright + SQLite + headless Chromium on Botkeep cloud hosting.

## What This Tests

- Python runtime compatibility
- Background execution (persistent process)
- Headless Chromium browser automation via Playwright
- SQLite persistent storage
- Memory and disk availability
- Browser lifecycle management (close after each job to free RAM)

## Local Setup

```bash
pip install -r requirements.txt
playwright install chromium
python main.py
```

## Botkeep Deployment

### 1. Project Files

Upload these files to your Botkeep project:

```
main.py
requirements.txt
```

### 2. Build / Install Command

In your Botkeep dashboard or `botkeep.yml`, set the install/build command:

```bash
pip install -r requirements.txt && playwright install --with-deps chromium
```

The `--with-deps` flag installs OS-level libraries required by Chromium. If Botkeep does not support apt/system package installation, try:

```bash
pip install -r requirements.txt && playwright install chromium
```

### 3. Start / Run Command

```bash
python main.py
```

Make sure the start command is configured as a **worker** or **background process** (not just a web server), since this script runs once and exits.

### 4. Persistent Storage

Botkeep provides a persistent filesystem (usually `/data` or similar). To ensure SQLite data survives restarts, set the environment variable:

```
DB_PATH=/data/jobs.db
```

Or modify `DB_PATH` in `main.py` to use the persistent mount path provided by your Botkeep plan.

### 5. Environment Variables

| Variable   | Default     | Description                              |
|------------|-------------|------------------------------------------|
| `DB_PATH`  | `jobs.db`   | Path to SQLite database file             |

### 6. Verification

After the process runs, check:

- Log output shows `Job 1 DONE` and `Job 2 DONE`
- SQLite file exists at the configured `DB_PATH`
- Query results:

```bash
python -c "import sqlite3; conn=sqlite3.connect('/data/jobs.db'); print(conn.execute('SELECT id,url,status,title FROM jobs').fetchall())"
```

## Output Example

```
[2026-10-09 12:00:01] Starting Botkeep test | Python 3.11.9 | RSS=45.2MB | disk_free=2048MB
[2026-10-09 12:00:01] Seeded 2 jobs into SQLite at jobs.db
[2026-10-09 12:00:01] Starting job 1: https://example.com | RSS=45.2MB | disk_free=2048MB
[2026-10-09 12:00:03] Job 1 DONE | title='Example Domain' | http=200 | RSS=120.5MB
[2026-10-09 12:00:03] Starting job 2: https://www.iana.org/domains/reserved | RSS=120.5MB | disk_free=2048MB
[2026-10-09 12:00:06] Job 2 DONE | title='IANA — IANA-managed Reserved Domains' | http=200 | RSS=118.3MB
[2026-10-09 12:00:06] All jobs processed. Results saved to jobs.db
[2026-10-09 12:00:06] Final: RSS=45.8MB | disk_free=2048MB
```

## Troubleshooting

- **ImportError: playwright** — Make sure `playwright install chromium` ran during build.
- **Browser launch fails** — Chromium may need `--no-sandbox`. Modify `main.py` to use `p.chromium.launch(headless=True, args=["--no-sandbox"])`.
- **ModuleNotFoundError: psutil** — Optional; install via `pip install psutil` or remove the import.
- **Database lost on restart** — Ensure `DB_PATH` points to the persistent storage volume, not `/tmp` or ephemeral disk.
- **Memory errors** — Botkeep plans with limited RAM may struggle with Chromium. The script closes the browser after each job to minimize peak usage.

## Files

| File              | Purpose                                  |
|-------------------|------------------------------------------|
| `main.py`         | Main script: job queue, browser, logging |
| `requirements.txt`| Python dependencies                      |
| `README.md`       | This file                                |
