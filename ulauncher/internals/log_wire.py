"""Wire format for log records an extension sends Ulauncher over its stdout/stderr pipes.

Ulauncher formats and colors them once, on its end. Output not in this form (a bare `print`,
an unhandled traceback) is passed through as-is.
"""

from __future__ import annotations

import logging
import re

SEPARATOR = "\x1f"  # ASCII unit separator: never occurs in log text
_FIELDS = ("%(levelno)d", "%(name)s", "%(pathname)s", "%(lineno)d", "%(funcName)s", "%(message)s")
FORMAT = SEPARATOR.join(_FIELDS)


class WireFormatter(logging.Formatter):
    """Renders a record as exactly one line, so one line Ulauncher reads is always one record."""

    def __init__(self) -> None:
        super().__init__(FORMAT)

    def format(self, record: logging.LogRecord) -> str:
        return super().format(record).replace("\\", "\\\\").replace("\n", "\\n")


def parse(line: str, ext_id: str) -> logging.LogRecord | None:
    """Rebuild the record an extension logged, or None if the line didn't come from its handler."""
    fields = line.split(SEPARATOR, len(_FIELDS) - 1)
    # isdecimal, not isdigit: int() rejects digits like "²"
    if len(fields) != len(_FIELDS) or not fields[0].isdecimal():
        return None

    levelno, name, pathname, lineno, func_name, message = (_unescape(field) for field in fields)
    return logging.LogRecord(
        name=name if name == ext_id else f"{ext_id}.{name}",
        level=int(levelno),
        pathname=pathname,
        lineno=int(lineno) if lineno.isdecimal() else 0,
        msg=message,
        args=None,
        exc_info=None,
        func=func_name,
    )


def _unescape(text: str) -> str:
    return re.sub(r"\\(.)", lambda match: "\n" if match.group(1) == "n" else match.group(1), text)
