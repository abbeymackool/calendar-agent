from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    google_credentials_path: str = Field(default="credentials_gmail.json", alias="GOOGLE_CREDENTIALS_PATH")
    google_calendar_disco_id: Optional[str] = Field(default=None, alias="GOOGLE_CALENDAR_DISCO_ID")
    google_calendar_upstairs_id: Optional[str] = Field(default=None, alias="GOOGLE_CALENDAR_UPSTAIRS_ID")

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

def require(name: str, value: Optional[str]) -> str:
    if not value:
        raise RuntimeError(
            f"Missing required setting: {name}. "
            f"Set it in .env (see .env.example) or export it in your shell."
        )
    return value
