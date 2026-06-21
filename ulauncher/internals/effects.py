from __future__ import annotations

from typing import TYPE_CHECKING, Final, Iterable, Literal, TypedDict, Union

# if type checking import Result
if TYPE_CHECKING:
    from typing_extensions import NotRequired

    from ulauncher.internals.result import Result


class EffectType:
    DO_NOTHING: Final = "effect:do_nothing"
    CLOSE_WINDOW: Final = "effect:close_window"
    SET_QUERY: Final = "effect:set_query"
    RENDER_RESULTS: Final = "effect:render_results"
    OPEN: Final = "effect:open"
    LEGACY_COPY: Final = "effect:legacy_copy"
    LEGACY_RUN_SCRIPT: Final = "effect:legacy_run_script"
    LEGACY_RUN_MANY: Final = "effect:legacy_run_many"
    LEGACY_ACTIVATE_CUSTOM: Final = "effect:legacy_activate_custom"


class DoNothing(TypedDict):
    type: Literal["effect:do_nothing"]


class CloseWindow(TypedDict):
    type: Literal["effect:close_window"]


class SetQuery(TypedDict):
    type: Literal["effect:set_query"]
    query: str


class RenderResults(TypedDict):
    type: Literal["effect:render_results"]
    results: list[Result]
    # True adds to the end of the current list, False (default) replaces the whole list.
    append: NotRequired[bool]
    # False while more batches are still coming for the same query.
    final: NotRequired[bool]


class Open(TypedDict):
    type: Literal["effect:open"]
    path: str


class LegacyCopy(TypedDict):
    type: Literal["effect:legacy_copy"]
    text: str


class LegacyRunScript(TypedDict):
    type: Literal["effect:legacy_run_script"]
    args: list[str]


class LegacyRunMany(TypedDict):
    type: Literal["effect:legacy_run_many"]
    effects: list[EffectMessage]


class LegacyActivateCustom(TypedDict):
    type: Literal["effect:legacy_activate_custom"]
    ref: int
    keep_app_open: bool


EffectMessage = Union[
    DoNothing,
    CloseWindow,
    SetQuery,
    RenderResults,
    Open,
    LegacyCopy,
    LegacyRunScript,
    LegacyRunMany,
    LegacyActivateCustom,
]

# Input format that we will convert to an EffectMessage. A plain iterable of Results becomes one
# render; a generator may also yield list[Result] batches to stream replace drafts (see
# api.extension.Extension._stream_response).
EffectMessageInput = Union[EffectMessage, bool, str, Iterable[Union["Result", "list[Result]"]]]


def do_nothing() -> DoNothing:
    return {"type": EffectType.DO_NOTHING}


def close_window() -> CloseWindow:
    return {"type": EffectType.CLOSE_WINDOW}


def set_query(query: str) -> SetQuery:
    if not isinstance(query, str):
        msg = f'Query argument "{query}" is invalid. It must be a string'
        raise TypeError(msg)
    return {"type": EffectType.SET_QUERY, "query": query}


def render_results(results: list[Result], append: bool = False, final: bool = True) -> RenderResults:
    return {"type": EffectType.RENDER_RESULTS, "results": results, "append": append, "final": final}


def open(item: str) -> Open:  # noqa: A001
    if not isinstance(item, str):
        msg = f'Open argument "{item}" is invalid. It must be a string'
        raise TypeError(msg)
    if not item:
        msg = "Open argument cannot be empty"
        raise ValueError(msg)
    return {"type": EffectType.OPEN, "path": item}
