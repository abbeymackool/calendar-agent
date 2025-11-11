import json
import re

from dateutil import parser as dtparse
from playwright.sync_api import sync_playwright

AUTH_PATH = "playwright/.auth/airbnb_state.json"
INBOX_URL = "https://www.airbnb.com/hosting/inbox"

# Regex for system updates, handles small wording variations:
RE_CHECKIN = re.compile(
    r"you updated .*check[\-\s]?in to ([\d: ]+[ap]m)\s+on\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", re.I
)
RE_CHECKOUT = re.compile(
    r"you updated .*check[\-\s]?out to ([\d: ]+[ap]m)\s+on\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", re.I
)


def parse_update(msg_text):
    m = RE_CHECKIN.search(msg_text)
    if m:
        t, d = m.groups()
        return {"type": "checkin_change", "when_str": f"{d} {t}"}
    m = RE_CHECKOUT.search(msg_text)
    if m:
        t, d = m.groups()
        return {"type": "checkout_change", "when_str": f"{d} {t}"}
    return None


def main(max_threads=20):
    results = []
    with sync_playwright() as p:
        b = p.chromium.launch(headless=False)
        ctx = b.new_context(storage_state=AUTH_PATH)
        page = ctx.new_page()
        page.goto(INBOX_URL, timeout=120_000)
        page.wait_for_load_state("networkidle")

        # Ensure we’re on Hosting inbox (not guest)
        try:
            hostTab = page.get_by_role("tab", name=re.compile("Hosting", re.I))
            if hostTab.count():
                hostTab.first.click()
                page.wait_for_load_state("networkidle")
        except:
            pass

        # Grab thread list items (robust-ish fallbacks)
        # Prefer items with data-testid, else role=link in the sidebar list
        items = page.locator('[data-testid="thread-item"]').or_(
            page.locator('[data-testid*="inbox-thread"]')
        )
        if items.count() == 0:
            items = page.get_by_role("link")  # fallback

        take = min(items.count(), max_threads)
        for i in range(take):
            try:
                thread = items.nth(i)
                thread.scroll_into_view_if_needed()
                thread.click()
                page.wait_for_load_state("networkidle")

                # Conversation header (guest / listing)
                header = ""
                try:
                    header_el = (
                        page.locator('[data-testid="thread-header"]')
                        .or_(page.locator("h1, h2, h3"))
                        .first
                    )
                    if header_el.count():
                        header = header_el.inner_text().strip()
                except:
                    pass

                # Collect recent messages (system + host/guest)
                msgs = page.locator('[data-testid="message-text"]').or_(
                    page.locator('[data-testid*="message"]')
                )
                count = min(msgs.count(), 30)
                for j in range(max(0, count - 10), count):  # last ~10 messages
                    text = msgs.nth(j).inner_text().strip()
                    upd = parse_update(text)
                    if upd:
                        # Try to parse datetime to ISO
                        try:
                            dt_local = dtparse.parse(upd["when_str"])
                            iso_when = dt_local.isoformat()
                        except:
                            iso_when = upd["when_str"]
                        results.append(
                            {
                                "thread_index": i,
                                "header": header,
                                "raw_text": text,
                                "update_type": upd["type"],
                                "new_time": iso_when,
                            }
                        )
            except Exception as e:
                # continue to next thread
                print(f"[warn] thread {i}: {e}")

        b.close()

    # Print JSON lines (easy to pipe/parse)
    for r in results:
        print(json.dumps(r, ensure_ascii=False))


if __name__ == "__main__":
    main()
