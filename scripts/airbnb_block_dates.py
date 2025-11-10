from playwright.sync_api import sync_playwright, TimeoutError
from datetime import datetime
import sys, time, platform, re

AUTH_PATH = "playwright/.auth/airbnb_state.json"
BASE_MULTI = "https://www.airbnb.com/multicalendar/53003871"  # Disco listing id
DISCO_NAME = "Design-Focused, Riverfront Loft Near Downtown"

def month_param(iso_date:str)->str:
    d = datetime.fromisoformat(iso_date)
    return d.strftime("%Y-%m-01")

def iso_to_label(iso_date:str)->str:
    d = datetime.fromisoformat(iso_date)
    day_fmt = "%-d" if platform.system() != "Windows" else "%#d"
    return d.strftime(f"%A, %B {day_fmt}, %Y")

def ensure_disco_selected(page):
    # Best-effort: if the listing chip/row is present, click it
    try:
        row = (page.get_by_text(DISCO_NAME, exact=True)
               .or_(page.get_by_role("link", name=DISCO_NAME))
               .or_(page.get_by_role("option", name=DISCO_NAME)))
        if row.count():
            row.first.scroll_into_view_if_needed()
            row.first.click(force=True, timeout=1500)
    except Exception:
        pass

def act_on_date(page, iso_date:str, make_available=False):
    label = iso_to_label(iso_date)
    # Prefer stable testid, fallback to aria-label
    cell = page.locator(f'[data-testid="calendar-day-{iso_date}"]')
    if cell.count() == 0:
        cell = page.get_by_label(label, exact=True)
    if cell.count() == 0:
        print(f"Could not locate {iso_date} ({label}).")
        return

    cell.first.scroll_into_view_if_needed()
    cell.first.click()
    page.wait_for_timeout(250)

    acted = False
    names = (["Available","Mark as available","Unblock","Save"]
             if make_available else
             ["Unavailable","Mark as unavailable","Block","Save"])
    for name in names:
        btns = page.get_by_role("button", name=re.compile(name, re.I))
        if btns.count():
            btns.first.click()
            acted = True
            break
    if not acted:
        switches = page.locator("button[aria-pressed], [role='switch']")
        if switches.count():
            switches.first.click()
            acted = True

    page.wait_for_timeout(250)
    save = page.get_by_role("button", name=re.compile("Save", re.I))
    if save.count():
        save.first.click()

    print(("Unblocked" if make_available else "Blocked"), iso_date)

def block_or_unblock(dates, make_available=False):
    with sync_playwright() as p:
        b = p.chromium.launch(headless=False)
        ctx = b.new_context(storage_state=AUTH_PATH)
        page = ctx.new_page()

        for d in dates:
            url = f"{BASE_MULTI}?month={month_param(d)}"
            page.goto(url, timeout=120_000)
            page.wait_for_load_state("networkidle")
            ensure_disco_selected(page)
            try:
                act_on_date(page, d, make_available=make_available)
            except TimeoutError:
                print(f"Timeout on {d}")
            time.sleep(0.2)

        ctx.storage_state(path=AUTH_PATH)
        b.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:\n  Block:   python scripts/airbnb_block_dates.py 2025-12-27 2025-12-28\n  Unblock: python scripts/airbnb_block_dates.py --unblock 2025-12-27")
        sys.exit(1)

    args = sys.argv[1:]
    make_available = False
    if args[0] == "--unblock":
        make_available = True
        args = args[1:]

    block_or_unblock(args, make_available=make_available)
