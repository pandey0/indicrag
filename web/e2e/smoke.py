"""Browser smoke test: ask a question, see a Sources list and the disclaimer. Needs the API (:8000) and web (:3000) running.

python3 web/e2e/smoke.py [screenshot.png]   (uses system Chrome via CHROME_BIN, default /usr/bin/google-chrome)
"""
import os
import sys

from playwright.sync_api import sync_playwright

shot = sys.argv[1] if len(sys.argv) > 1 else None
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get("CHROME_BIN", "/usr/bin/google-chrome"), headless=True)
    page = b.new_page()
    page.goto("http://localhost:3000")
    page.get_by_label("Your question").fill("आयुष्मान भारत में प्रति परिवार कितना कवरेज मिलता है?")
    page.get_by_role("button", name="Ask").click()
    page.get_by_role("heading", name="Sources").wait_for(timeout=20000)
    assert page.locator("ol li").count() >= 1, "no sources rendered"
    assert "Not legal or financial advice" in page.content() or "not legal or financial advice" in page.content().lower()
    if shot:
        page.screenshot(path=shot, full_page=True)
    print("smoke ok:", page.locator("ol li").count(), "sources")
    b.close()
