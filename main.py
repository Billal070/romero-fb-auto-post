import sqlite3
import shutil
import sys
import os
from datetime import datetime

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

DB_PATH = os.environ.get("DB_PATH", "jobs.db")
PAGES = [
    "https://example.com",
    "https://www.iana.org/domains/reserved",
]


def log(message):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {message}", flush=True)


def get_memory_info():
    if HAS_PSUTIL:
        proc = psutil.Process(os.getpid())
        rss_mb = proc.memory_info().rss / (1024 * 1024)
        return f"RSS={rss_mb:.1f}MB"
    return "RSS=N/A"


def get_disk_info():
    try:
        if os.name == "nt":
            usage = shutil.disk_usage(os.environ.get("SystemDrive", "C:") + "\\")
        else:
            usage = shutil.disk_usage("/")
        free_mb = usage.free / (1024 * 1024)
        return f"disk_free={free_mb:.0f}MB"
    except Exception:
        return "disk=N/A"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            title TEXT,
            error TEXT,
            http_status INTEGER,
            started_at TEXT,
            finished_at TEXT
        )"""
    )
    conn.commit()
    return conn


def seed_jobs(conn):
    count = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    if count == 0:
        now = datetime.utcnow().isoformat()
        for url in PAGES:
            conn.execute(
                "INSERT INTO jobs (url, status, started_at) VALUES (?, 'pending', ?)",
                (url, now),
            )
        conn.commit()
        log(f"Seeded {len(PAGES)} jobs into SQLite at {DB_PATH}")


def fetch_page(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context()
            page = context.new_page()
            response = page.goto(url, wait_until="domcontentloaded", timeout=30000)
            title = page.title()
            http_status = response.status if response else None
            return title, http_status, None
        except Exception as e:
            return None, None, str(e)
        finally:
            browser.close()


def run_jobs():
    conn = init_db()
    seed_jobs(conn)

    pending = conn.execute(
        "SELECT id, url FROM jobs WHERE status != 'done' ORDER BY id"
    ).fetchall()

    if not pending:
        log("No pending jobs found. All done.")

    for job_id, url in pending:
        log(f"Starting job {job_id}: {url} | {get_memory_info()} | {get_disk_info()}")
        started = datetime.utcnow().isoformat()

        title, http_status, error = fetch_page(url)

        if error:
            conn.execute(
                "UPDATE jobs SET status='error', error=?, finished_at=? WHERE id=?",
                (error, datetime.utcnow().isoformat(), job_id),
            )
            log(f"Job {job_id} FAILED | error={error} | {get_memory_info()}")
        else:
            conn.execute(
                "UPDATE jobs SET status='done', title=?, http_status=?, finished_at=? WHERE id=?",
                (title, http_status, datetime.utcnow().isoformat(), job_id),
            )
            log(f"Job {job_id} DONE | title='{title}' | http={http_status} | {get_memory_info()}")

        conn.commit()

    conn.close()
    log(f"All jobs processed. Results saved to {DB_PATH}")
    log(f"Final: {get_memory_info()} | {get_disk_info()}")


if __name__ == "__main__":
    if not HAS_PLAYWRIGHT:
        log("ERROR: playwright not installed. Run: pip install -r requirements.txt && playwright install chromium")
        sys.exit(1)
    if not HAS_PSUTIL:
        log("WARNING: psutil not installed, memory metrics will show N/A")
    log(f"Starting Botkeep test | Python {sys.version.split()[0]} | {get_memory_info()} | {get_disk_info()}")
    run_jobs()
