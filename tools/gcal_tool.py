# tools/gcal_tool.py
import os
from datetime import datetime, timedelta, time
from typing import Optional, Dict, Any, List

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/calendar"]

# ---------------- Core service ----------------
def _svc():
    creds = None
    # calendar token lives in project root
    if os.path.exists("token_calendar.json"):
        creds = Credentials.from_authorized_user_file("token_calendar.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # calendar creds file (client id/secret)
            flow = InstalledAppFlow.from_client_secrets_file("credentials_calendar.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token_calendar.json", "w") as f:
            f.write(creds.to_json())
    return build("calendar", "v3", credentials=creds, cache_discovery=False)

# ---------------- Basic helpers ----------------
def get_cal_id(summary: str) -> str:
    s = _svc(); page = None
    while True:
        resp = s.calendarList().list(pageToken=page).execute()
        for it in resp.get("items", []):
            if it.get("summary") == summary:
                return it["id"]
        page = resp.get("nextPageToken")
        if not page:
            break
    raise RuntimeError(f"Calendar '{summary}' not found")

def find_event_by_private(cal_id: str, key: str, value: str,
                          time_min: Optional[datetime] = None,
                          time_max: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
    s = _svc()
    if not time_min:
        time_min = (datetime.now().astimezone() - timedelta(days=365))
    if not time_max:
        time_max = (datetime.now().astimezone() + timedelta(days=365))
    resp = s.events().list(
        calendarId=cal_id,
        timeMin=time_min.isoformat(),
        timeMax=time_max.isoformat(),
        singleEvents=True,
        maxResults=2500
    ).execute()
    for e in resp.get("items", []):
        priv = e.get("extendedProperties", {}).get("private", {})
        if priv.get(key) == value:
            return e
    return None

def upsert_event(cal_id: str, body: Dict[str, Any], key: str, value: str) -> Dict[str, Any]:
    s = _svc()
    body.setdefault("extendedProperties", {}).setdefault("private", {})[key] = value
    ex = find_event_by_private(cal_id, key, value)
    if ex:
        return s.events().patch(calendarId=cal_id, eventId=ex["id"], body=body).execute()
    return s.events().insert(calendarId=cal_id, body=body).execute()

def delete_event_by_private(cal_id: str, key: str, value: str) -> bool:
    s = _svc()
    ex = find_event_by_private(cal_id, key, value)
    if ex:
        s.events().delete(calendarId=cal_id, eventId=ex["id"]).execute()
        return True
    return False

def delete_all_events_by_private(cal_id: str, key: str, value: str) -> int:
    """Delete ALL events where extendedProperties.private[key] == value. Returns count."""
    s = _svc()
    deleted = 0
    resp = s.events().list(
        calendarId=cal_id,
        timeMin=(datetime.now().astimezone() - timedelta(days=365)).isoformat(),
        timeMax=(datetime.now().astimezone() + timedelta(days=365)).isoformat(),
        singleEvents=True,
        maxResults=2500
    ).execute()
    for e in resp.get("items", []):
        priv = e.get("extendedProperties", {}).get("private", {})
        if priv.get(key) == value:
            s.events().delete(calendarId=cal_id, eventId=e["id"]).execute()
            deleted += 1
    return deleted

def delete_events_by_private_prefix(cal_id: str, key: str, prefix: str,
                                    time_min: Optional[datetime] = None,
                                    time_max: Optional[datetime] = None) -> int:
    """
    Delete ALL events where extendedProperties.private[key] startswith(prefix).
    Optionally limit to a time window [time_min, time_max].
    Returns number of deleted events.
    """
    s = _svc()
    if not time_min:
        time_min = (datetime.now().astimezone() - timedelta(days=365))
    if not time_max:
        time_max = (datetime.now().astimezone() + timedelta(days=365))

    deleted = 0
    resp = s.events().list(
        calendarId=cal_id,
        timeMin=time_min.isoformat(),
        timeMax=time_max.isoformat(),
        singleEvents=True,
        maxResults=2500
    ).execute()

    for e in resp.get("items", []):
        priv = e.get("extendedProperties", {}).get("private", {})
        val = priv.get(key, "")
        if isinstance(val, str) and val.startswith(prefix):
            s.events().delete(calendarId=cal_id, eventId=e["id"]).execute()
            deleted += 1
    return deleted

# ---------------- De-dupe / adopt helpers ----------------
def _list_events_in_window(cal_id: str, start: datetime, end: datetime) -> List[Dict[str, Any]]:
    s = _svc()
    resp = s.events().list(
        calendarId=cal_id,
        timeMin=start.isoformat(),
        timeMax=end.isoformat(),
        singleEvents=True,
        maxResults=2500
    ).execute()
    return resp.get("items", []) or []

from typing import Tuple  # keep this import

def _day_bounds(day: datetime.date, tzinfo) -> Tuple[datetime, datetime]:
    start = datetime.combine(day, time(0, 0), tzinfo=tzinfo)
    end = datetime.combine(day, time(23, 59, 59), tzinfo=tzinfo)
    return start, end

def find_same_day_event_by_summary_location(cal_id: str, summary: str, location: Optional[str],
                                            day: datetime.date, tzinfo) -> Optional[Dict[str, Any]]:
    """Find an existing manual or agent event on that calendar DAY with the same summary (and optional location)."""
    tmin, tmax = _day_bounds(day, tzinfo)
    for e in _list_events_in_window(cal_id, tmin, tmax):
        if e.get("status") == "cancelled":
            continue
        if e.get("summary", "").strip().upper() != summary.strip().upper():
            continue
        if location and e.get("location", "") != location:
            continue
        # accept the first match
        return e
    return None

def patch_event_times(cal_id: str, event: Dict[str, Any],
                      start_dt: datetime, end_dt: datetime, tz: str,
                      ensure_private: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Patch an event's time window and optionally ensure private extendedProperties."""
    s = _svc()
    body = {
        "start": {"dateTime": start_dt.isoformat(), "timeZone": tz},
        "end":   {"dateTime": end_dt.isoformat(),   "timeZone": tz},
    }
    if ensure_private:
        body.setdefault("extendedProperties", {}).setdefault("private", {}).update(ensure_private)
    return s.events().patch(calendarId=cal_id, eventId=event["id"], body=body).execute()

def upsert_or_modify_buffer(cal_id: str, summary: str, location: str,
                            desired_start: datetime, desired_end: datetime,
                            booking_key: str, tz: str) -> Dict[str, Any]:
    """
    - If an event with same summary/location exists on the same day: PATCH its start/end (adopt manual).
    - Else: insert a new one.
    Also stamps extendedProperties.private.booking_key so future runs are idempotent.
    """
    existing = find_same_day_event_by_summary_location(
        cal_id, summary, location, desired_start.date(), desired_start.tzinfo
    )
    ensure_priv = {"source": "agent", "type": "peerspace", "booking_key": booking_key}
    if existing:
        return patch_event_times(cal_id, existing, desired_start, desired_end, tz, ensure_private=ensure_priv)
    # no manual/agent one -> insert
    body = {
        "summary": summary,
        "location": location,
        "start": {"dateTime": desired_start.isoformat(), "timeZone": tz},
        "end":   {"dateTime": desired_end.isoformat(),   "timeZone": tz},
        "extendedProperties": {"private": ensure_priv},
    }
    # keep "booking_key" as idempotency key
    return upsert_event(cal_id, body, "booking_key", booking_key)

def upsert_or_attach_all_day(cal_id: str, summary: str, date_str: str,
                             private_keys: Dict[str, str]) -> Dict[str, Any]:
    """
    Ensure there is ONE all-day event on date_str.

    Adoption behavior:
      - If ANY all-day event exists that day (regardless of its current title),
        adopt it by merging our private keys AND set the title to the requested `summary`
        (so we can show 'AM EVENT' / 'EVENT', etc.).
      - Else, insert a new all-day event with that `summary`.

    Idempotency:
      - Uses ps_block_key (or booking_key) to avoid duplicates on insert.
    """
    s = _svc()
    day = datetime.fromisoformat(date_str)  # YYYY-MM-DD
    tmin = datetime.combine(day.date(), time(0, 0)).astimezone()
    tmax = datetime.combine(day.date(), time(23, 59, 59)).astimezone()

    # Look for any all-day event that day
    for e in _list_events_in_window(cal_id, tmin, tmax):
        if e.get("status") == "cancelled":
            continue
        st = e.get("start", {})
        if "date" in st:  # all-day event
            # Adopt and normalize title: patch summary + merge private keys
            merged_priv = {**e.get("extendedProperties", {}).get("private", {}), **private_keys}
            body = {
                "summary": summary,  # <-- rename to desired label (e.g., 'AM EVENT')
                "extendedProperties": {"private": merged_priv}
            }
            return s.events().patch(calendarId=cal_id, eventId=e["id"], body=body).execute()

    # Not found -> insert new all-day event
    body = {
        "summary": summary,
        "start": {"date": date_str},
        "end":   {"date": (datetime.fromisoformat(date_str).date() + timedelta(days=1)).isoformat()},
        "extendedProperties": {"private": private_keys},
    }
    # use ps_block_key if provided for idempotency; otherwise booking_key
    id_key = private_keys.get("ps_block_key") or private_keys.get("booking_key")
    keyname = "ps_block_key" if "ps_block_key" in private_keys else "booking_key"
    return upsert_event(cal_id, body, keyname, id_key)