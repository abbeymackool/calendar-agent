# list_cals.py
import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Use calendar-specific creds/token
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
CREDS_PATH = "credentials_calendar.json"
TOKEN_PATH = "token_calendar.json"

def svc():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
    return build("calendar", "v3", credentials=creds, cache_discovery=False)

if __name__ == "__main__":
    s = svc()
    for it in s.calendarList().list().execute().get("items", []):
        print(it["summary"])