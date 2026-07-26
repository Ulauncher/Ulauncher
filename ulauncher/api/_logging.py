"""Shared logging setup for the extension API and deprecation warnings."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from ulauncher.internals import log_wire
from ulauncher.utils.logging_color_formatter import ColoredFormatter


def get_extension_handler() -> logging.Handler:
    """The handler every logger in the extension process writes through."""
    handler = logging.StreamHandler()
    # Ulauncher imports this module too, where nothing parses the wire format back
    in_extension_process = bool(os.getenv("SOCKETPAIR_FD"))
    handler.setFormatter(log_wire.WireFormatter() if in_extension_process else ColoredFormatter())
    return handler


def get_extension_logger() -> logging.Logger:
    """Get or create a logger for the extension."""
    # The env var id is always set, but fallback anyway on the dirname
    log_name = os.getenv("ULAUNCHER_EXTENSION_ID") or Path(sys.argv[0]).resolve().parent.name

    logger = logging.getLogger(log_name)

    # Own handler below, so don't also forward records to the root logger's handler
    logger.propagate = False

    # Only add handler if not already present (avoid duplicates on re-import)
    if not logger.handlers:
        logger.addHandler(get_extension_handler())

    return logger
