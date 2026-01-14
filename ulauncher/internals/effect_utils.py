from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Final, Iterable, cast

from ulauncher.internals.effects import (
    EffectMessage,
    EffectMessageInput,
    EffectType,
    close_window,
    do_nothing,
    set_query,
)
from ulauncher.utils.eventbus import EventBus

if TYPE_CHECKING:
    from ulauncher.internals.result import Result

_VALID_EFFECT_TYPES: Final = frozenset(getattr(EffectType, key) for key in EffectType.__annotations__)
_events = EventBus()
_logger = logging.getLogger()


def is_valid(effect_msg: Any) -> bool:
    return isinstance(effect_msg, dict) and effect_msg.get("type") in _VALID_EFFECT_TYPES


def should_close(effect_msg: EffectMessage | list[Result]) -> bool:
    """Whether or not the effect should close the window."""
    if isinstance(effect_msg, list):
        return False
    if isinstance(effect_msg, dict):
        if effect_msg.get("type") in (EffectType.DO_NOTHING, EffectType.SET_QUERY):
            return False
        if effect_msg.get("type") == EffectType.LEGACY_RUN_MANY:
            effect_list = cast("list[EffectMessage | list[Result]]", effect_msg.get("data", []))
            return all(map(should_close, effect_list))
    return True


def handle(effect_msg: EffectMessage, prevent_close: bool = False) -> None:
    """Process effects by dispatching to appropriate handlers."""
    event_type = effect_msg.get("type", "")
    data = effect_msg.get("data")
    has_valid_type = event_type in _VALID_EFFECT_TYPES

    if event_type == EffectType.SET_QUERY and isinstance(data, str):
        _events.emit("app:set_query", data)

    elif event_type == EffectType.OPEN and isinstance(data, str):
        from ulauncher.utils.launch_detached import open_detached

        open_detached(data)

    elif event_type == EffectType.LEGACY_COPY and isinstance(data, str):
        _events.emit("app:clipboard_store", data)

    elif event_type == EffectType.LEGACY_RUN_SCRIPT and isinstance(data, list):
        from ulauncher.modes.shortcuts.run_script import run_script

        run_script(*data)
    elif event_type == EffectType.LEGACY_RUN_MANY and isinstance(data, list):
        for effect in cast("list[EffectMessage | list[Result]]", data):
            if isinstance(effect, list):
                _events.emit("app:show_results", effect)
            else:
                handle(effect, True)

    elif not has_valid_type:
        _logger.warning("Unknown effect type: %s", event_type)
    elif event_type not in (EffectType.DO_NOTHING, EffectType.CLOSE_WINDOW):
        _logger.warning("Invalid data for effect type: %s, %s", event_type, data)

    if has_valid_type and should_close(effect_msg) and not prevent_close:
        _events.emit("app:close_launcher")


def convert_to_effect_message(input_data: EffectMessageInput | None) -> EffectMessage | list[Result]:
    """Normalize input format that supports boolean and string to represent effects and iterable lists for results"""
    if isinstance(input_data, bool) or input_data is None:
        return do_nothing() if input_data else close_window()
    if isinstance(input_data, str):
        return set_query(input_data)
    if isinstance(input_data, dict):
        if is_valid(input_data):
            return cast("EffectMessage", input_data)  # TypedDict unions can't be narrowed by runtime checks
        err_msg = f"Invalid effect message dict: {input_data}"
        raise ValueError(err_msg)
    return list(cast("Iterable[Result]", input_data))  # collect/flatten iterators to lists
