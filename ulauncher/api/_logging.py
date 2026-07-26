"""Shared logging setup for the extension API and deprecation warnings."""

from __future__ import annotations

import logging
import os

from ulauncher.utils.logging_color_formatter import ColoredFormatter


def get_extension_logger() -> logging.Logger:
    """Get or create a logger for the extension."""
    logger = logging.getLogger(os.environ["ULAUNCHER_EXTENSION_ID"])

    # Own handler below, so don't also forward records to the root logger's handler
    logger.propagate = False

    # Only add handler if not already present (avoid duplicates on re-import)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(ColoredFormatter())
        logger.addHandler(handler)

    return logger
