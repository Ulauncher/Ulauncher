from __future__ import annotations

import logging
import random


def mkcolor(color: int, bold: bool = False) -> str:
    if bold:
        color = f"1;{color}"  # type: ignore[assignment]
    return f"\x1b[{color}m"


class ColoredFormatter(logging.Formatter):
    formats = {
        logging.DEBUG: ("ℹ️", 34),  # blue # noqa: RUF001
        logging.INFO: ("ℹ️", 37),  # white # noqa: RUF001
        logging.WARNING: ("⚠️", 33),  # yellow
        logging.ERROR: ("⚠️", 31),  # red
        logging.CRITICAL: ("⚠️", 31),  # red
    }

    def __init__(self) -> None:
        # Varying parts are injected as record fields, so this is built once, not per record
        super().__init__("%(asctime)s %(color_prefix)s %(message)s %(color_suffix)s")
        self._name_colors: dict[str, int] = {}

    def _name_color(self, name: str) -> int:
        if name not in self._name_colors:
            # Own generator, so the same name keeps its color without reseeding the shared one
            self._name_colors[name] = random.Random(name).randint(32, 37)
        return self._name_colors[name]

    def format(self, record: logging.LogRecord) -> str:
        # Great reference for terminal colors: https://chrisyeh96.github.io/2020/03/28/terminal-colors.html
        symbol, level_color = self.formats.get(record.levelno, ("", 0))
        prefix = f"{symbol}  {mkcolor(level_color, True)}{record.levelname}{mkcolor(0)}"
        if record.name != "root":
            name = record.name[len("ulauncher.") :] if record.name.startswith("ulauncher.") else record.name
            prefix += f"{mkcolor(self._name_color(record.name), True)} {name}{mkcolor(0)}:"
        # Raw extension output has no source location, only a stream name
        location = f"{record.funcName}:{record.lineno}" if record.lineno else record.funcName
        record.__dict__["color_prefix"] = prefix
        record.__dict__["color_suffix"] = f"{mkcolor(2)}{location}{mkcolor(0)}"  # 2 means faded
        return super().format(record)
