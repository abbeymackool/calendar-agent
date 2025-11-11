"""
Script: gmail_sync
Purpose: Placeholder for Gmail → Calendar/DB sync. Clear scaffolding for novices.

Data Shapes:
- (Define models here as needed; reuse core types for consistency)
"""

from __future__ import annotations

from calendar_agent.config import settings
from calendar_agent.utils.logging import setup_logging


def run():
    setup_logging(settings.log_level)
    # TODO: implement Gmail ingestion (messages → normalized records)
    print("gmail_sync: not yet implemented. Add your logic here.")


if __name__ == "__main__":
    run()
