from __future__ import annotations

import logging
from typing import Any

from ulauncher.internals.result import ActionMessage

logger = logging.getLogger()


def do_nothing() -> ActionMessage:
    return {"type": "action:do_nothing"}


def close_window() -> ActionMessage:
    return {"type": "action:close_window"}


def set_query(query: str) -> ActionMessage:
    if not isinstance(query, str):
        msg = f'Query argument "{query}" is invalid. It must be a string'
        logger.error(msg)
        raise TypeError(msg)
    return {"type": "action:set_query", "data": query}


def copy(text: str) -> ActionMessage:
    if not isinstance(text, str):
        msg = f'Copy argument "{text}" is invalid. It must be a string'
        logger.error(msg)
        raise TypeError(msg)
    return {"type": "action:clipboard_store", "data": text}


def open(item: str) -> ActionMessage:  # noqa: A001
    if not item:
        msg = "Open argument cannot be empty"
        logger.error(msg)
        raise ValueError(msg)
    if not isinstance(item, str):
        msg = f'Open argument "{item}" is invalid. It must be a string'
        logger.error(msg)
        raise TypeError(msg)
    return {"type": "action:open", "data": item}


def run_script(script: str, args: str = "") -> ActionMessage:
    if not script:
        msg = "Script argument cannot be empty"
        logger.error(msg)
        raise ValueError(msg)
    if not isinstance(script, str):
        msg = f'Script argument "{script}" is invalid. It must be a string'
        logger.error(msg)
        raise TypeError(msg)
    return {"type": "action:legacy_run_script", "data": [script, args]}


def action_list(actions: list[Any]) -> ActionMessage:
    return {"type": "action:legacy_run_many", "data": actions}
