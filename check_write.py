from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import os, datetime

SCOPES=["https://www.googleapis.com/auth/calendar"]

def svc():
    creds=None
    if os.path.exists("token.json"):
        creds=Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow=InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds=flow.run_local_server(port=0)
        with open("token.json","w") as f: f.write(creds.to_json())
    return build("calendar","v3",credentials=creds,cache_discovery=False)

s=svc()
print("Write access OK")
