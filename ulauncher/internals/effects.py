from __future__ import annotations

from typing import TYPE_CHECKING, Final, Iterable, Literal, TypedDict, Union, overload

# if type checking import Result
if TYPE_CHECKING:
    from typing_extensions import NotRequired

    from ulauncher.internals.result import Result


class EffectType:
    DO_NOTHING: Final = "effect:do_nothing"
    CLOSE_WINDOW: Final = "effect:close_window"
    SET_QUERY: Final = "effect:set_query"
    SET_TRIGGER_QUERY: Final = "effect:set_trigger_query"
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


class SetTriggerQuery(TypedDict):
    """Sent by extensions, which can't know their keywords. ExtensionMode turns it into a SetQuery."""

    type: Literal["effect:set_trigger_query"]
    trigger_id: str
    argument: str


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


NonRenderEffectMessage = Union[
    DoNothing,
    CloseWindow,
    SetQuery,
    SetTriggerQuery,
    Open,
    LegacyCopy,
    LegacyRunScript,
    LegacyRunMany,
    LegacyActivateCustom,
]

EffectMessage = Union[NonRenderEffectMessage, RenderResults]

# Input format that we will convert to an EffectMessage. A plain iterable of Results becomes one
# render; a generator may also yield list[Result] batches to stream replace drafts (see
# api.extension.Extension._stream_response).
EffectMessageInput = Union[EffectMessage, Iterable[Union["Result", "list[Result]"]]]


def do_nothing() -> DoNothing:
    return {"type": EffectType.DO_NOTHING}


def close_window() -> CloseWindow:
    return {"type": EffectType.CLOSE_WINDOW}


@overload
def set_query(query: str) -> SetQuery: ...


@overload
def set_query(query: str, trigger_id: str) -> SetTriggerQuery: ...


def set_query(query: str, trigger_id: str | None = None) -> SetQuery | SetTriggerQuery:
    """
    Set the query in the input field.

    :param query: The query argument for the trigger, or the whole query if trigger_id is not given
        (deprecated for extensions, since they can't know the keyword the user set for the trigger)
    :param trigger_id: The trigger whose keyword (as set by the user) to prefix the argument with
    """
    if not isinstance(query, str):
        msg = f'Query argument "{query}" is invalid. It must be a string'
        raise TypeError(msg)
    if trigger_id is None:
        return {"type": EffectType.SET_QUERY, "query": query}
    if not isinstance(trigger_id, str):
        msg = f'Trigger id "{trigger_id}" is invalid. It must be a string'
        raise TypeError(msg)
    return {"type": EffectType.SET_TRIGGER_QUERY, "trigger_id": trigger_id, "argument": query}


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
