import logging
import os
import sys
import time
import resource

from flask import Flask, jsonify
from playwright.sync_api import sync_playwright, Error as PlaywrightError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

TEST_URL = "https://example.com"


def get_rss_mb():
    try:
        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return usage / 1024.0
    except Exception:
        return -1.0


@app.get("/health")
def health():
    logger.info("Health check requested")
    return jsonify({"status": "ok", "service": "railway-browser-test"})


@app.get("/run-test")
def run_test():
    logger.info("Starting browser test for %s", TEST_URL)
    start = time.monotonic()

    try:
        with sync_playwright() as p:
            logger.info("Launching headless Chromium")
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            logger.info("Browser launched")

            try:
                page = browser.new_page()
                logger.info("Navigating to %s", TEST_URL)
                response = page.goto(TEST_URL, wait_until="domcontentloaded", timeout=30000)
                title = page.title()
                http_status = response.status if response else None
                logger.info("Navigation complete | title='%s' | http=%s", title, http_status)
            finally:
                browser.close()
                logger.info("Browser closed")

        elapsed = time.monotonic() - start
        rss = get_rss_mb()
        logger.info("Test completed in %.2fs | peak RSS=%.1fMB", elapsed, rss)

        return jsonify({
            "success": True,
            "title": title,
            "http_status": http_status,
            "url": TEST_URL,
            "elapsed_seconds": round(elapsed, 3),
            "peak_rss_mb": round(rss, 1),
        })

    except PlaywrightError as e:
        logger.error("Playwright error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500
    except Exception as e:
        logger.error("Unexpected error: %s", e, exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    logger.info("Starting server on 0.0.0.0:%d | Python %s", port, sys.version.split()[0])
    app.run(host="0.0.0.0", port=port, threaded=True)
