# gmail_sync.py
# Reads labeled Gmail messages (hello@discoloft.com), creates/updates events on your Google Calendars.

import os, json, re, base64
from datetime import datetime, timedelta as TD
from dateutil import parser as dtp
from dateutil.tz import gettz
from email.header import decode_header
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from tools.gcal_tool import (
    get_cal_id,
    upsert_event,
    delete_event_by_private,
    delete_all_events_by_private,
    delete_events_by_private_prefix,   # <-- new import
)
from tools.rules import block_dates_for_event

# ---- Gmail auth uses work creds ----
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDS_PATH_GMAIL = "credentials_gmail.json"
TOKEN_PATH_GMAIL = "token_gmail.json"

# ---- Calendar names (must match exactly in Google) ----
CAL_DISCO    = "Disco Bookings"
CAL_UPSTAIRS = "Upstairs Bookings"
CAL_BLOCK    = "Block on Airbnb"
TZ = "America/Detroit"

# ---- Gmail nested labels (as they appear in Gmail) ----
LABELS = {
    # Peerspace
    "PS_EVENT_CONF":    "Peerspace/Event Bookings",
    "PS_PHOTO_CONF":    "Peerspace/Photo Bookings",
    "PS_UPDATE":        "Peerspace/Booking Updates",
    "PS_CANCEL":        "Peerspace/Cancellations",
    # Airbnb
    "AB_DISCO_CONF":    "Airbnb/Disco Bookings",
    "AB_UPSTAIRS_CONF": "Airbnb/Upstairs Bookings",
    "AB_CANCEL":        "Airbnb/Cancellations",
}

STATE_FILE = "gmail_state.json"  # to avoid reprocessing same emails

# ---------------- Gmail helpers ----------------
def gmail_service():
    creds = None
    if os.path.exists(TOKEN_PATH_GMAIL):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH_GMAIL, GMAIL_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH_GMAIL, GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH_GMAIL, "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds, cache_discovery=False)

def get_label_map(svc):
    labs = svc.users().labels().list(userId="me").execute().get("labels", [])
    return {l["name"]: l["id"] for l in labs}

def list_messages(svc, label_name, newer_than_days=30):
    lid = get_label_map(svc).get(label_name)
    if not lid:
        print(f"[warn] Gmail label not found: {label_name}")
        return []
    q = f"newer_than:{newer_than_days}d"
    resp = svc.users().messages().list(userId="me", labelIds=[lid], q=q, maxResults=50).execute()
    return resp.get("messages", []) or []

def fetch_message(svc, msg_id):
    return svc.users().messages().get(userId="me", id=msg_id, format="full").execute()

def header_value(msg, name):
    for h in msg.get("payload", {}).get("headers", []):
        if h.get("name","").lower() == name.lower():
            val = h.get("value","")
            parts = decode_header(val)
            return "".join([(p.decode(enc) if isinstance(p, bytes) else p) for p, enc in parts])
    return ""

def body_text(msg):
    def _decode(b64):
        return base64.urlsafe_b64decode(b64 + "===")
    payload = msg.get("payload", {})
    parts = [payload] + (payload.get("parts") or [])
    texts = []
    for p in parts:
        mt = p.get("mimeType", "")
        data = p.get("body", {}).get("data")
        if not data: continue
        try:
            decoded = _decode(data).decode("utf-8", errors="ignore")
        except Exception:
            continue
        if mt.startswith("text/plain"):
            texts.append(decoded)
        elif mt.startswith("text/html") and not texts:
            texts.append(re.sub("<[^>]+>", " ", decoded))
    return "\n".join(texts).strip()

def load_state():
    return json.load(open(STATE_FILE)) if os.path.exists(STATE_FILE) else {"seen": []}

def save_state(state):
    json.dump(state, open(STATE_FILE,"w"), indent=2)

# ---------------- Parsers ----------------
# Peerspace listing titles
PS_EVENT_TITLE = "Design-Focused Loft 🥂 Private Event Space"
PS_PHOTO_TITLE = "Design-Focused Loft 🧨 Photo + Video"

# Example line we capture:
# "Sat, Nov 9, 2025 12:00 PM - 2:00 PM EST"
RE_PS_WINDOW = re.compile(
    r"([A-Za-z]{3},\s+[A-Za-z]{3}\s+\d{1,2},\s+\d{4})\s+(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*(\d{1,2}:\d{2}\s*[AP]M)",
    re.I,
)

def parse_peerspace(text, subject):
    """
    Return dict with kind ('EVENT'|'PHOTOSHOOT'), guest, start, end (tz-attached).
    """
    kind = "EVENT" if PS_EVENT_TITLE in text else ("PHOTOSHOOT" if PS_PHOTO_TITLE in text else None)
    if not kind:
        return None

    # Guest from subject line: "... confirmed with <Guest> on ..."
    m_guest = re.search(r"confirmed with .*?([A-Za-z][\w.\s-]+)\s+on", subject, re.I)
    guest = m_guest.group(1).strip() if m_guest else "Guest"

    m = RE_PS_WINDOW.search(text)
    if not m:
        return None
    day_str, s_str, e_str = m.groups()

    tz = gettz(TZ)
    start = dtp.parse(f"{day_str} {s_str}").replace(tzinfo=tz)
    end   = dtp.parse(f"{day_str} {e_str}").replace(tzinfo=tz)
    return {"platform":"peerspace","kind":kind,"guest":guest,"start":start,"end":end}

# Airbnb parsing
RE_AB_LISTING_DISCO    = re.compile(r"Design-Focused, Riverfront Loft Near Downtown", re.I)
RE_AB_LISTING_UPSTAIRS = re.compile(r"Hip Loft w Detroit River Views", re.I)
RE_AB_CHECKIN  = re.compile(r"Check-?in\s+[A-Za-z]{3},?\s*([A-Za-z]{3}\s+\d{1,2})\s+(\d{1,2}:\d{2}\s*[AP]M)", re.I)
RE_AB_CHECKOUT = re.compile(r"Check-?out\s+[A-Za-z]{3},?\s*([A-Za-z]{3}\s+\d{1,2})\s+(\d{1,2}:\d{2}\s*[AP]M)", re.I)
RE_AB_SUBJECT_GUEST = re.compile(r"Reservation confirmed - .*? ([A-Za-z][\w.\s-]+) arrives", re.I)
RE_AB_CANCEL_RES_CODE = re.compile(r"Canceled:\s*Reservation\s+([A-Z0-9]+)", re.I)

def parse_airbnb_confirmation(text, subject):
    listing = "disco" if RE_AB_LISTING_DISCO.search(text) else ("upstairs" if RE_AB_LISTING_UPSTAIRS.search(text) else None)
    if not listing: return None
    mg = RE_AB_SUBJECT_GUEST.search(subject)
    guest = mg.group(1).strip() if mg else "Guest"
    m_in = RE_AB_CHECKIN.search(text); m_out = RE_AB_CHECKOUT.search(text)
    if not (m_in and m_out): return None
    today = datetime.now()
    ci_day, ci_time = m_in.groups(); co_day, co_time = m_out.groups()
    ci = dtp.parse(f"{ci_day} {today.year} {ci_time} {TZ}")
    co = dtp.parse(f"{co_day} {today.year} {co_time} {TZ}")
    if co < ci: co = co.replace(year=co.year+1)
    return {"platform":"airbnb","listing":listing,"guest":guest,"checkin":ci,"checkout":co}

def parse_airbnb_cancel(text, subject):
    m = RE_AB_CANCEL_RES_CODE.search(subject)
    code = m.group(1) if m else None
    listing = "disco" if RE_AB_LISTING_DISCO.search(text) else ("upstairs" if RE_AB_LISTING_UPSTAIRS.search(text) else None)
    return {"platform":"airbnb","listing":listing,"booking_key":code} if listing else None

# ---------------- Actions ----------------
def upsert_peerspace(kind, guest, start, end):
    disco_id = get_cal_id(CAL_DISCO)
    block_id = get_cal_id(CAL_BLOCK)

    # Desired buffer window on Disco:
    if kind == "EVENT":
        buf_start = (start - TD(hours=1))
        buf_end   = (end   + TD(hours=2))   # 2h after for events
        base_title = "EVENT"
    else:
        buf_start = (start - TD(hours=1))
        buf_end   = (end   + TD(hours=1))   # 1h after for photoshoots
        base_title = "PHOTOSHOOT"

    booking_key = f"ps|{guest}|{start.date()}"

    # 1) Disco buffer: adopt or insert (and patch times if needed)
    from tools.gcal_tool import upsert_or_modify_buffer
    upsert_or_modify_buffer(
        disco_id,
        summary=base_title,
        location="1-hr buffer",
        desired_start=buf_start,
        desired_end=buf_end,
        booking_key=booking_key,
        tz=TZ,
    )

    # 2) Airbnb all-day blocks (adopt or insert)
    from tools.rules import block_dates_for_event
    for d in sorted(block_dates_for_event(start, end)):
        # Decide title for that all-day block:
        # If the blocked day is the day BEFORE the booking date, and booking starts before 1 PM,
        # label as "AM EVENT"/"AM PHOTOSHOOT". Otherwise keep base title.
        is_prev_day = (dtp.isoparse(d).date() == (start.date() - TD(days=1)).date())
        starts_before_1pm = start.hour < 13  # 1 PM cutoff
        block_title = (f"AM {base_title}") if (is_prev_day and starts_before_1pm) else base_title

        # Private keys to attach (idempotent + manageable)
        priv = {
            "managedBy": "CalendarAgent",
            "type": "AirbnbBlock",
            "booking_key": booking_key,
            "block_date": d,
            "ps_block_key": f"{booking_key}|{d}",   # unique per date
        }
        from tools.gcal_tool import upsert_or_attach_all_day
        upsert_or_attach_all_day(block_id, summary=block_title, date_str=d, private_keys=priv)

def upsert_airbnb(listing, guest, checkin, checkout):
    if listing == "disco":
        cal_id = get_cal_id(CAL_DISCO)
        types = [
            ("ab_res", {"summary": guest,
                        "start":{"dateTime":checkin.isoformat(), "timeZone": TZ},
                        "end":{"dateTime":checkout.isoformat(), "timeZone": TZ}}),
            ("ab_checkin_buffer", {"summary":"CHECK-IN BUFFER",
                        "start":{"dateTime":(checkin - TD(hours=2)).isoformat(), "timeZone": TZ},
                        "end":{"dateTime":checkin.isoformat(), "timeZone": TZ}}),
            ("ab_turnover", {"summary":"TURNOVER",
                        "start":{"dateTime":checkout.isoformat(), "timeZone": TZ},
                        "end":{"dateTime":(checkout + TD(hours=2)).isoformat(), "timeZone": TZ}}),
        ]
        for tkey, body in types:
            body.setdefault("extendedProperties", {}).setdefault("private", {}).update({
                "source":"agent","type":tkey,"booking_key": f"ab|{guest}|{checkin.date()}"
            })
            upsert_event(cal_id, body, "type_booking", f"{tkey}|{guest}|{checkin.date()}")
    else:
        cal_id = get_cal_id(CAL_UPSTAIRS)
        body = {
            "summary": guest,
            "start":{"dateTime":checkin.isoformat(), "timeZone": TZ},
            "end":{"dateTime":checkout.isoformat(), "timeZone": TZ},
            "extendedProperties":{"private":{"source":"agent","type":"ab_res","booking_key": f"ab|{guest}|{checkin.date()}" }}
        }
        upsert_event(cal_id, body, "type_booking", f"ab_res|{guest}|{checkin.date()}")

def cancel_airbnb(listing, booking_key_hint):
    cal_id = get_cal_id(CAL_DISCO if listing=="disco" else CAL_UPSTAIRS)
    delete_event_by_private(cal_id, "booking_key", booking_key_hint)
    delete_event_by_private(cal_id, "type_booking", f"ab_res|{booking_key_hint}")
    delete_event_by_private(cal_id, "type_booking", f"ab_checkin_buffer|{booking_key_hint}")
    delete_event_by_private(cal_id, "type_booking", f"ab_turnover|{booking_key_hint}")

# ---------------- Handlers (Peerspace) ----------------

def handle_ps_cancel(text, subject):
    """
    Remove the Disco buffer + all Airbnb block days for this Peerspace booking.
    We derive the same booking_key we use on create: ps|<Guest>|<YYYY-MM-DD>
    """
    r = parse_peerspace(text, subject)
    if not r:
        return
    guest = r["guest"]
    bk = f"ps|{guest}|{r['start'].date()}"
    # Remove buffer on Disco
    delete_all_events_by_private(get_cal_id(CAL_DISCO), "booking_key", bk)
    # Remove all related block days
    delete_all_events_by_private(get_cal_id(CAL_BLOCK), "booking_key", bk)

def handle_ps_update(text, subject):
    """
    Update flow:
      1) Sweep old buffers/blocks for *this guest* within a window around the new date.
      2) Insert new buffers/blocks for the updated times.
    """
    r = parse_peerspace(text, subject)
    if not r:
        return

    guest = r["guest"]
    start = r["start"]
    # prefix matches any prior booking_key for this guest, e.g., "ps|Alex Lee|"
    prefix = f"ps|{guest}|"
    window_days = 90
    time_min = (start - TD(days=window_days)).replace(hour=0, minute=0, second=0, microsecond=0)
    time_max = (start + TD(days=window_days)).replace(hour=23, minute=59, second=59, microsecond=0)

    # Sweep (Disco + Block) for any prior entries for this guest in the window
    delete_events_by_private_prefix(get_cal_id(CAL_DISCO), "booking_key", prefix, time_min, time_max)
    delete_events_by_private_prefix(get_cal_id(CAL_BLOCK), "booking_key", prefix, time_min, time_max)

    # Recreate with new times
    upsert_peerspace(r["kind"], r["guest"], r["start"], r["end"])

# ---------------- Main poll ----------------
def main():
    svc = gmail_service()
    state = load_state(); seen = set(state.get("seen", []))

    plans = [
        # Peerspace confirmations
        ("PS_EVENT_CONF",    lambda t,s: (lambda r: upsert_peerspace(r["kind"], r["guest"], r["start"], r["end"]) if r and r["kind"]=="EVENT" else None)(parse_peerspace(t,s))),
        ("PS_PHOTO_CONF",    lambda t,s: (lambda r: upsert_peerspace(r["kind"], r["guest"], r["start"], r["end"]) if r and r["kind"]=="PHOTOSHOOT" else None)(parse_peerspace(t,s))),
        # Peerspace updates/cancellations
        ("PS_UPDATE",        handle_ps_update),
        ("PS_CANCEL",        handle_ps_cancel),

        # Airbnb confirmations/cancellations
        ("AB_DISCO_CONF",    lambda t,s: (lambda r: upsert_airbnb(r["listing"], r["guest"], r["checkin"], r["checkout"]) if r else None)(parse_airbnb_confirmation(t,s))),
        ("AB_UPSTAIRS_CONF", lambda t,s: (lambda r: upsert_airbnb(r["listing"], r["guest"], r["checkin"], r["checkout"]) if r else None)(parse_airbnb_confirmation(t,s))),
        ("AB_CANCEL",        lambda t,s: (lambda r: cancel_airbnb(r["listing"], r.get("booking_key") or "") if r else None)(parse_airbnb_cancel(t,s))),
    ]

    for key, handler in plans:
        msgs = list_messages(svc, LABELS[key], newer_than_days=30)
        for m in msgs:
            mid = m["id"]
            if mid in seen:
                continue
            msg = fetch_message(svc, mid)
            subj = header_value(msg, "Subject")
            text = body_text(msg)
            try:
                handler(text, subj)
            except Exception as e:
                print(f"[warn] handler error for {key}: {e}")
            seen.add(mid)

    state["seen"] = list(seen)
    save_state(state)
    print("Gmail sync done.")

if __name__ == "__main__":
    main()