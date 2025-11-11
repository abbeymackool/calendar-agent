from playwright.sync_api import sync_playwright

AUTH_PATH = "playwright/.auth/airbnb_state.json"
LISTING_CAL_URL = "https://www.airbnb.com/hosting/listings/53003871/calendar"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(storage_state=AUTH_PATH)
    page = ctx.new_page()
    page.goto(LISTING_CAL_URL, timeout=120_000)
    print("Loaded:", page.url, "| Title:", page.title())
    b.close()
