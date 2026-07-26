from __future__ import annotations

import logging
import random

from ulauncher.utils.lru_cache import lru_cache


def mkcolor(color: int, bold: bool = False) -> str:
    if bold:
        color = f"1;{color}"  # type: ignore[assignment]
    return f"\x1b[{color}m"


@lru_cache
def _name_color(name: str) -> int:
    """Ensure the same name gets the same color every time."""
    # Own generator, because seeding the shared one would make every other caller's draw depend
    # on the last name logged. Cached because seeding costs more than formatting the whole record.
    return random.Random(name).randint(32, 37)


class ColoredFormatter(logging.Formatter):
    formats = {
        logging.DEBUG: ("ℹ️", 34),  # blue # noqa: RUF001
        logging.INFO: ("ℹ️", 37),  # white # noqa: RUF001
        logging.WARNING: ("⚠️", 33),  # yellow
        logging.ERROR: ("⚠️", 31),  # red
        logging.CRITICAL: ("⚠️", 31),  # red
    }

    def __init__(self) -> None:
        # The parts that vary per record are injected as record fields below, so this is built once
        super().__init__("%(asctime)s %(color_prefix)s %(message)s %(color_suffix)s")

    def format(self, record: logging.LogRecord) -> str:
        # Great reference for terminal colors: https://chrisyeh96.github.io/2020/03/28/terminal-colors.html
        symbol, level_color = self.formats.get(record.levelno, ("", 0))
        prefix = f"{symbol}  {mkcolor(level_color, True)}{record.levelname}{mkcolor(0)}"
        if record.name != "root":
            name = record.name[len("ulauncher.") :] if record.name.startswith("ulauncher.") else record.name
            prefix += f"{mkcolor(_name_color(record.name), True)} {name}{mkcolor(0)}:"
        record.__dict__["color_prefix"] = prefix
        record.__dict__["color_suffix"] = f"{mkcolor(2)}{record.funcName}:{record.lineno}{mkcolor(0)}"  # 2 is faded
        return super().format(record)
