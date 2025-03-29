from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger()


def copy(text: str) -> dict[str, str]:
    if not text:
        msg = "Copy argument cannot be empty"
        logger.error(msg)
        raise ValueError(msg)
    if type(text) is not str:
        msg = f'Copy argument "{text}" is invalid. It must be a string'
        logger.error(msg)
        raise TypeError(msg)
    return {"type": "action:clipboard_store", "data": text}


def open(item: str) -> dict[str, str]:  # noqa: A001
    if not item:
        msg = "Open argument cannot be empty"
        logger.error(msg)
        raise ValueError(msg)
    if type(item) is not str:
        msg = f'Open argument "{item}" is invalid. It must be a string'
        logger.error(msg)
        raise TypeError(msg)
    return {"type": "action:open", "data": item}


def run_script(script: str, args: str = "") -> dict[str, str | list[str]]:
    if not script:
        msg = "Script argument cannot be empty"
        logger.error(msg)
        raise ValueError(msg)
    if type(script) is not str:
        msg = f'Script argument "{script}" is invalid. It must be a string'
        logger.error(msg)
        raise TypeError(msg)
    return {"type": "action:legacy_run_script", "data": [script, args]}


def action_list(actions: list[Any]) -> dict[str, Any]:
    return {"type": "action:legacy_run_many", "data": actions}
