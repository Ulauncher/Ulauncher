from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Final, Iterable, Literal, TypedDict, Union

# if type checking import Result
if TYPE_CHECKING:
    from ulauncher.internals.result import Result


class EffectType:
    DO_NOTHING: Final = "effect:do_nothing"
    CLOSE_WINDOW: Final = "effect:close_window"
    SET_QUERY: Final = "effect:set_query"
    OPEN: Final = "effect:open"
    COPY: Final = "effect:clipboard_store"
    LEGACY_RUN_SCRIPT: Final = "effect:legacy_run_script"
    LEGACY_RUN_MANY: Final = "effect:legacy_run_many"
    LEGACY_ACTIVATE_CUSTOM: Final = "effect:legacy_activate_custom"


class DoNothing(TypedDict):
    type: Literal["effect:do_nothing"]


class CloseWindow(TypedDict):
    type: Literal["effect:close_window"]


class SetQuery(TypedDict):
    type: Literal["effect:set_query"]
    data: str


class Open(TypedDict):
    type: Literal["effect:open"]
    data: str


class Copy(TypedDict):
    type: Literal["effect:clipboard_store"]
    data: str


class LegacyRunScript(TypedDict):
    type: Literal["effect:legacy_run_script"]
    data: list[str]


class LegacyRunMany(TypedDict):
    type: Literal["effect:legacy_run_many"]
    data: list[Any]  # list of other EffectMessages (can't be expressed with TypedDict)


class LegacyActivateCustom(TypedDict):
    type: Literal["effect:legacy_activate_custom"]
    ref: int
    keep_app_open: bool


EffectMessage = Union[
    DoNothing,
    CloseWindow,
    SetQuery,
    Open,
    Copy,
    LegacyRunScript,
    LegacyRunMany,
    LegacyActivateCustom,
]

# Input format that we will convert to an EffectMessage
EffectMessageInput = Union[EffectMessage, bool, str, Iterable["Result"]]

logger = logging.getLogger()


def do_nothing() -> DoNothing:
    return {"type": EffectType.DO_NOTHING}


def close_window() -> CloseWindow:
    return {"type": EffectType.CLOSE_WINDOW}


def set_query(query: str) -> SetQuery:
    if not isinstance(query, str):
        msg = f'Query argument "{query}" is invalid. It must be a string'
        logger.error(msg)
        raise TypeError(msg)
    return {"type": EffectType.SET_QUERY, "data": query}


def copy(text: str) -> Copy:
    if not isinstance(text, str):
        msg = f'Copy argument "{text}" is invalid. It must be a string'
        logger.error(msg)
        raise TypeError(msg)
    return {"type": EffectType.COPY, "data": text}


def open(item: str) -> Open:  # noqa: A001
    if not isinstance(item, str):
        msg = f'Open argument "{item}" is invalid. It must be a string'
        logger.error(msg)
        raise TypeError(msg)
    if not item:
        msg = "Open argument cannot be empty"
        logger.error(msg)
        raise ValueError(msg)
    return {"type": EffectType.OPEN, "data": item}


def run_script(script: str, args: str = "") -> LegacyRunScript:
    if not isinstance(script, str):
        msg = f'Script argument "{script}" is invalid. It must be a string'
        logger.error(msg)
        raise TypeError(msg)
    if not script:
        msg = "Script argument cannot be empty"
        logger.error(msg)
        raise ValueError(msg)
    return {"type": EffectType.LEGACY_RUN_SCRIPT, "data": [script, args]}


def effect_list(effects: list[Any]) -> LegacyRunMany:
    return {"type": EffectType.LEGACY_RUN_MANY, "data": effects}
