"""
Module: logging
Purpose: Centralized, beginner-friendly logging setup with colored levels.

Data Shapes: None
"""

from __future__ import annotations

import logging
import sys
from typing import Literal


def setup_logging(level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO") -> None:
    """
    Initialize root logger with a simple, readable format.

    Args:
        level: Log verbosity. One of "DEBUG", "INFO", "WARNING", "ERROR".
    """
    root = logging.getLogger()
    if root.handlers:
        # Already configured (avoid duplicate handlers when called multiple times)
        return

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
