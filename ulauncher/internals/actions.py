from __future__ import annotations

import logging
from typing import Any, Literal, TypedDict, Union


class DoNothing(TypedDict):
    type: Literal["action:do_nothing"]


class CloseWindow(TypedDict):
    type: Literal["action:close_window"]


class SetQuery(TypedDict):
    type: Literal["action:set_query"]
    data: str


class Open(TypedDict):
    type: Literal["action:open"]
    data: str


class Copy(TypedDict):
    type: Literal["action:clipboard_store"]
    data: str


class LegacyRunScript(TypedDict):
    type: Literal["action:legacy_run_script"]
    data: list[str]


class LegacyRunMany(TypedDict):
    type: Literal["action:legacy_run_many"]
    data: list[Any]  # list of other ActionMessages (can't be expressed with TypedDict)


class ActivateCustom(TypedDict):
    type: Literal["action:activate_custom"]
    ref: int
    keep_app_open: bool


class LaunchTriggerAction(TypedDict):
    type: Literal["action:launch_trigger"]


ActionMessage = Union[
    DoNothing,
    CloseWindow,
    SetQuery,
    Open,
    Copy,
    LegacyRunScript,
    LegacyRunMany,
    ActivateCustom,
    LaunchTriggerAction,
]

logger = logging.getLogger()


def do_nothing() -> DoNothing:
    return {"type": "action:do_nothing"}


def close_window() -> CloseWindow:
    return {"type": "action:close_window"}


def set_query(query: str) -> SetQuery:
    if not isinstance(query, str):
        msg = f'Query argument "{query}" is invalid. It must be a string'
        logger.error(msg)
        raise TypeError(msg)
    return {"type": "action:set_query", "data": query}


def copy(text: str) -> Copy:
    if not isinstance(text, str):
        msg = f'Copy argument "{text}" is invalid. It must be a string'
        logger.error(msg)
        raise TypeError(msg)
    return {"type": "action:clipboard_store", "data": text}


def open(item: str) -> Open:  # noqa: A001
    if not isinstance(item, str):
        msg = f'Open argument "{item}" is invalid. It must be a string'
        logger.error(msg)
        raise TypeError(msg)
    if not item:
        msg = "Open argument cannot be empty"
        logger.error(msg)
        raise ValueError(msg)
    return {"type": "action:open", "data": item}


def run_script(script: str, args: str = "") -> LegacyRunScript:
    if not isinstance(script, str):
        msg = f'Script argument "{script}" is invalid. It must be a string'
        logger.error(msg)
        raise TypeError(msg)
    if not script:
        msg = "Script argument cannot be empty"
        logger.error(msg)
        raise ValueError(msg)
    return {"type": "action:legacy_run_script", "data": [script, args]}


def action_list(actions: list[Any]) -> LegacyRunMany:
    return {"type": "action:legacy_run_many", "data": actions}
