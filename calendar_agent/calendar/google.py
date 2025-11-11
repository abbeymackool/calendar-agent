"""
Module: calendar.google
Purpose: Minimal, well-documented Google Calendar client wrappers.

Data Shapes:
- CalendarRef: core.types.CalendarRef
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request  # needed for token refresh

from calendar_agent.config import settings
from calendar_agent.core.types import CalendarRef

LOGGER = logging.getLogger(__name__)
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _get_service():
    """
    Build and return a Google Calendar API service client.

    On first run, performs OAuth flow; subsequent runs reuse token.
    """
    creds: Optional[Credentials] = None
    try:
        creds = Credentials.from_authorized_user_file(settings.GOOGLE_TOKEN_FILE, SCOPES)  # type: ignore[arg-type]
    except Exception:
        creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(settings.GOOGLE_CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(settings.GOOGLE_TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def create_event(cal: CalendarRef, summary: str, start: datetime, end: datetime, description: str = "") -> str:
    """
    Create a single event.

    Returns:
        event_id (str): The created event's ID.
    """
    service = _get_service()
    body: dict[str, Any] = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start.isoformat()},
        "end": {"dateTime": end.isoformat()},
    }
    result = service.events().insert(calendarId=cal.calendar_id, body=body).execute()
    event_id = result.get("id", "")
    LOGGER.info("Created event %s in '%s'", event_id, cal.name)
    return event_id


def update_event(cal: CalendarRef, event_id: str, **patch: Any) -> None:
    """Patch an existing event with Google event fields via **patch**."""
    service = _get_service()
    event = service.events().get(calendarId=cal.calendar_id, eventId=event_id).execute()
    event.update(patch)
    service.events().update(calendarId=cal.calendar_id, eventId=event_id, body=event).execute()
    LOGGER.info("Updated event %s in '%s'", event_id, cal.name)


def list_between(cal: CalendarRef, start: datetime, end: datetime):
    """Yield events between start and end."""
    service = _get_service()
    request = service.events().list(
        calendarId=cal.calendar_id,
        timeMin=start.isoformat(),
        timeMax=end.isoformat(),
        singleEvents=True,
        orderBy="startTime",
    )
    while True:
        resp = request.execute()
        for e in resp.get("items", []):
            yield e
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
        request = service.events().list_next(previous_request=request, previous_response=resp)
