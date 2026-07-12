"""Shared logging setup for the extension API and deprecation warnings."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from ulauncher.utils.logging_color_formatter import ColoredFormatter


def get_extension_logger() -> logging.Logger:
    """Get or create a logger for the extension."""
    # The env var id is always set, but fallback anyway on the dirname
    log_name = os.getenv("ULAUNCHER_EXTENSION_ID") or Path(sys.argv[0]).resolve().parent.name

    logger = logging.getLogger(log_name)

    # Only add handler if not already present (avoid duplicates on re-import)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(ColoredFormatter())
        logger.addHandler(handler)

    return logger
