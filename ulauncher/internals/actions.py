from __future__ import annotations

import logging
from typing import Any, Final, Literal, TypedDict, Union


class ActionType:
    DO_NOTHING: Final = "action:do_nothing"
    CLOSE_WINDOW: Final = "action:close_window"
    SET_QUERY: Final = "action:set_query"
    LAUNCH_TRIGGER: Final = "action:launch_trigger"
    OPEN: Final = "action:open"
    COPY: Final = "action:clipboard_store"
    LEGACY_RUN_SCRIPT: Final = "action:legacy_run_script"
    LEGACY_RUN_MANY: Final = "action:legacy_run_many"
    LEGACY_ACTIVATE_CUSTOM: Final = "action:legacy_activate_custom"


class DoNothing(TypedDict):
    type: Literal["action:do_nothing"]


class CloseWindow(TypedDict):
    type: Literal["action:close_window"]


class SetQuery(TypedDict):
    type: Literal["action:set_query"]
    data: str


class LaunchTrigger(TypedDict):
    type: Literal["action:launch_trigger"]
    args: list[str]
    ext_id: str


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


class LegacyActivateCustom(TypedDict):
    type: Literal["action:legacy_activate_custom"]
    ref: int
    keep_app_open: bool


ActionMessage = Union[
    DoNothing,
    CloseWindow,
    SetQuery,
    Open,
    Copy,
    LaunchTrigger,
    LegacyRunScript,
    LegacyRunMany,
    LegacyActivateCustom,
]

logger = logging.getLogger()
_VALID_ACTION_TYPES: Final = frozenset(getattr(ActionType, key) for key in ActionType.__annotations__)


def is_valid(action_msg: Any) -> bool:
    return isinstance(action_msg, dict) and action_msg.get("type") in _VALID_ACTION_TYPES


def do_nothing() -> DoNothing:
    return {"type": ActionType.DO_NOTHING}


def close_window() -> CloseWindow:
    return {"type": ActionType.CLOSE_WINDOW}


def set_query(query: str) -> SetQuery:
    if not isinstance(query, str):
        msg = f'Query argument "{query}" is invalid. It must be a string'
        logger.error(msg)
        raise TypeError(msg)
    return {"type": ActionType.SET_QUERY, "data": query}


def copy(text: str) -> Copy:
    if not isinstance(text, str):
        msg = f'Copy argument "{text}" is invalid. It must be a string'
        logger.error(msg)
        raise TypeError(msg)
    return {"type": ActionType.COPY, "data": text}


def open(item: str) -> Open:  # noqa: A001
    if not isinstance(item, str):
        msg = f'Open argument "{item}" is invalid. It must be a string'
        logger.error(msg)
        raise TypeError(msg)
    if not item:
        msg = "Open argument cannot be empty"
        logger.error(msg)
        raise ValueError(msg)
    return {"type": ActionType.OPEN, "data": item}


def run_script(script: str, args: str = "") -> LegacyRunScript:
    if not isinstance(script, str):
        msg = f'Script argument "{script}" is invalid. It must be a string'
        logger.error(msg)
        raise TypeError(msg)
    if not script:
        msg = "Script argument cannot be empty"
        logger.error(msg)
        raise ValueError(msg)
    return {"type": ActionType.LEGACY_RUN_SCRIPT, "data": [script, args]}


def action_list(actions: list[Any]) -> LegacyRunMany:
    return {"type": ActionType.LEGACY_RUN_MANY, "data": actions}
