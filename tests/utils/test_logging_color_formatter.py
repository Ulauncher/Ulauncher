import logging
import random

from ulauncher.utils.logging_color_formatter import ColoredFormatter


def test_format__leaves_the_shared_random_state_alone() -> None:
    record = logging.LogRecord("ulauncher.some.module", logging.WARNING, "/src/mod.py", 42, "hi", None, None)
    state = random.getstate()

    ColoredFormatter().format(record)

    assert random.getstate() == state
