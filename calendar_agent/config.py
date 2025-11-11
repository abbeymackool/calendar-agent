"""
Module: config
Purpose: Load settings from .env or OS environment (developer-friendly).
"""

from __future__ import annotations

import os
from typing import List
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv


class Settings(BaseModel):
    # OAuth files for Google Calendar
    GOOGLE_CREDENTIALS_FILE: str = Field(..., description="Path to OAuth client JSON")
    GOOGLE_TOKEN_FILE: str = Field(..., description="Path to OAuth token JSON")

    # Exactly three calendars you use
    CAL_DISCO_BOOKINGS: str
    CAL_UPSTAIRS_BOOKINGS: str
    CAL_BLOCK_ON_AIRBNB: str

    LOG_LEVEL: str = "INFO"

    def as_safe_dict(self):
        return {
            "GOOGLE_CREDENTIALS_FILE": self.GOOGLE_CREDENTIALS_FILE,
            "GOOGLE_TOKEN_FILE": self.GOOGLE_TOKEN_FILE,
            "CAL_DISCO_BOOKINGS": self.CAL_DISCO_BOOKINGS,
            "CAL_UPSTAIRS_BOOKINGS": self.CAL_UPSTAIRS_BOOKINGS,
            "CAL_BLOCK_ON_AIRBNB": self.CAL_BLOCK_ON_AIRBNB,
            "LOG_LEVEL": self.LOG_LEVEL,
        }


def _required_keys() -> List[str]:
    return [
        "GOOGLE_CREDENTIALS_FILE",
        "GOOGLE_TOKEN_FILE",
        "CAL_DISCO_BOOKINGS",
        "CAL_UPSTAIRS_BOOKINGS",
        "CAL_BLOCK_ON_AIRBNB",
    ]


def _collect_missing(keys: List[str]) -> List[str]:
    return [k for k in keys if not os.getenv(k)]


def load_settings() -> Settings:
    # Load .env from the project root (current working dir)
    load_dotenv(override=False)

    missing = _collect_missing(_required_keys())
    if missing:
        lines = "\n".join(f"- {k}" for k in missing)
        raise RuntimeError(
            "Missing required environment variables.\n"
            "Create and populate a .env file in the repo root with the following keys:\n"
            f"{lines}\n"
        )
    try:
        return Settings(
            GOOGLE_CREDENTIALS_FILE=os.environ["GOOGLE_CREDENTIALS_FILE"],
            GOOGLE_TOKEN_FILE=os.environ["GOOGLE_TOKEN_FILE"],
            CAL_DISCO_BOOKINGS=os.environ["CAL_DISCO_BOOKINGS"],
            CAL_UPSTAIRS_BOOKINGS=os.environ["CAL_UPSTAIRS_BOOKINGS"],
            CAL_BLOCK_ON_AIRBNB=os.environ["CAL_BLOCK_ON_AIRBNB"],
            LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
        )
    except ValidationError as e:
        raise RuntimeError(f"Invalid configuration: {e}") from e


# Singleton for app use
settings = load_settings()
