from pathlib import Path

from playwright.sync_api import sync_playwright

AUTH_PATH = "playwright/.auth/airbnb_state.json"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(storage_state=AUTH_PATH if Path(AUTH_PATH).exists() else None)
    page = context.new_page()
    page.goto("https://www.airbnb.com/login", timeout=120_000)

    if Path(AUTH_PATH).exists():
        print(
            "Session file exists. If you see you're already logged in, just close the browser window."
        )
    else:
        print("Complete login in the opened browser window.")
        input("When you finish logging in, come back here and press Enter...")

    context.storage_state(path=AUTH_PATH)
    print(f"Saved login state to {AUTH_PATH}")
    browser.close()
