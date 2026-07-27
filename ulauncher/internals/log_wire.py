"""Wire format for log records an extension sends Ulauncher over its stdout/stderr pipes.

Ulauncher formats and colors them once, on its end. Output not in this form (a bare `print`,
an unhandled traceback) is passed through as-is.
"""

from __future__ import annotations

import json
import logging


class WireFormatter(logging.Formatter):
    """Renders a record as one JSON line, so one line Ulauncher reads is always one record."""

    def __init__(self) -> None:
        # Only the message, so the traceback logger.exception appends stays inside that field
        super().__init__("%(message)s")

    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(
            {
                "levelno": record.levelno,
                "name": record.name,
                "pathname": record.pathname,
                "lineno": record.lineno,
                "funcName": record.funcName,
                "message": super().format(record),
            }
        )


def parse(line: str, ext_id: str) -> logging.LogRecord | None:
    """Rebuild the record an extension logged, or None if the line didn't come from its handler."""
    try:
        fields = json.loads(line)
        name = fields["name"]
        if not isinstance(name, str):
            return None
        # Sub-loggers of the extension's own logger are already namespaced
        namespaced = name == ext_id or name.startswith(f"{ext_id}.")
        return logging.LogRecord(
            name=name if namespaced else f"{ext_id}.{name}",
            level=int(fields["levelno"]),
            pathname=fields["pathname"],
            lineno=int(fields["lineno"]),
            msg=fields["message"],
            args=None,
            exc_info=None,
            func=fields["funcName"],
        )
    except (KeyError, TypeError, ValueError):
        return None
