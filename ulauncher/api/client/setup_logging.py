import os
import logging

from ulauncher.utils.logging import ColoredFormatter


def setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(ColoredFormatter())
    logging.basicConfig(
        level=logging.DEBUG if os.getenv('VERBOSE') else logging.WARNING,
        handlers=[handler]
    )
