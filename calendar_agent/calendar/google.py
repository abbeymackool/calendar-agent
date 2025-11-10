from __future__ import annotations
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os, pathlib
from calendar_agent.models.event import CalendarEvent
from calendar_agent.config import settings

SCOPES = ["https://www.googleapis.com/auth/calendar"]

def _creds():
    token_path = pathlib.Path("token_gcal.json")
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(settings.google_credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json())
    return creds

def _service():
    return build("calendar", "v3", credentials=_creds())

def create(event: CalendarEvent) -> str:
    body = {
        "summary": event.summary,
        "description": event.description,
        "start": {"dateTime": event.start.isoformat()},
        "end": {"dateTime": event.end.isoformat()},
        "location": event.location,
    }
    svc = _service()
    created = svc.events().insert(calendarId=event.calendar_id, body=body).execute()
    return created["id"]

def update(provider_id: str, event: CalendarEvent) -> None:
    body = {
        "summary": event.summary,
        "description": event.description,
        "start": {"dateTime": event.start.isoformat()},
        "end": {"dateTime": event.end.isoformat()},
        "location": event.location,
    }
    svc = _service()
    svc.events().patch(calendarId=event.calendar_id, eventId=provider_id, body=body).execute()

def delete(calendar_id: str, provider_id: str) -> None:
    svc = _service()
    svc.events().delete(calendarId=calendar_id, eventId=provider_id).execute()
