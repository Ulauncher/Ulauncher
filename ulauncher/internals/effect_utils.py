from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final, Iterable, cast

from ulauncher.internals.effects import (
    EffectMessage,
    EffectMessageInput,
    EffectType,
    close_window,
    do_nothing,
    render_results,
    set_query,
)
from ulauncher.utils.eventbus import EventBus

if TYPE_CHECKING:
    from typing_extensions import TypeGuard

    from ulauncher.internals.result import Result

_VALID_EFFECT_TYPES: Final = frozenset(getattr(EffectType, key) for key in EffectType.__annotations__)
_events = EventBus()


def is_effect_message(value: Any) -> TypeGuard[EffectMessage]:
    return isinstance(value, dict) and value.get("type") in _VALID_EFFECT_TYPES


def should_close(effect_msg: EffectMessage) -> bool:
    """Whether or not the effect should close the window."""
    if effect_msg.get("type") in (EffectType.DO_NOTHING, EffectType.SET_QUERY, EffectType.RENDER_RESULTS):
        return False
    if effect_msg["type"] == EffectType.LEGACY_RUN_MANY:
        return all(map(should_close, effect_msg["effects"]))
    return True


def is_valid_input_effect(effect_msg: EffectMessage) -> bool:
    """Whether the effect is a valid input query response (non-interruptive)"""
    if effect_msg["type"] == EffectType.LEGACY_RUN_MANY:
        effects = effect_msg.get("effects")
        return isinstance(effects, list) and all(
            is_effect_message(effect) and is_valid_input_effect(effect) for effect in effects
        )
    if effect_msg["type"] == EffectType.RENDER_RESULTS:
        return isinstance(effect_msg.get("results"), list)
    return effect_msg["type"] == EffectType.DO_NOTHING


def handle(effect_msg: EffectMessage, prevent_close: bool = False) -> None:
    """Process effects by dispatching to appropriate handlers."""

    if effect_msg["type"] == EffectType.SET_QUERY:
        _events.emit("app:set_query", effect_msg["query"])

    elif effect_msg["type"] == EffectType.OPEN:
        from ulauncher.utils.launch_detached import open_detached

        open_detached(effect_msg["path"])

    elif effect_msg["type"] == EffectType.LEGACY_COPY:
        _events.emit("app:copy_and_close", effect_msg["text"])

    elif effect_msg["type"] == EffectType.LEGACY_RUN_SCRIPT:
        from ulauncher.modes.shortcuts.run_script import run_script

        run_script(*effect_msg["args"])
    elif effect_msg["type"] == EffectType.RENDER_RESULTS:
        _events.emit("app:show_results", effect_msg["results"])

    elif effect_msg["type"] == EffectType.LEGACY_RUN_MANY:
        for effect in effect_msg["effects"]:
            handle(effect, True)

    if should_close(effect_msg) and not prevent_close:
        _events.emit("app:close_launcher")


def convert_to_effect_message(input_data: EffectMessageInput | None) -> EffectMessage:
    """Normalize input format that supports boolean and string to represent effects and iterable lists for results"""
    if isinstance(input_data, bool) or input_data is None:
        return do_nothing() if input_data else close_window()
    if isinstance(input_data, str):
        return set_query(input_data)
    if isinstance(input_data, dict):
        if is_effect_message(input_data):
            return input_data
        err_msg = f"Invalid effect message dict: {input_data}"
        raise ValueError(err_msg)
    return render_results(list(cast("Iterable[Result]", input_data)))  # collect/flatten iterators to lists
