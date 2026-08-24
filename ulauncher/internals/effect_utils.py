from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

from ulauncher.internals.effects import (
    EffectMessage,
    EffectType,
    NonRenderEffectMessage,
)
from ulauncher.utils.eventbus import EventBus

if TYPE_CHECKING:
    from typing_extensions import TypeGuard

_VALID_EFFECT_TYPES: Final = frozenset(getattr(EffectType, key) for key in EffectType.__annotations__)
# Mirrors the required keys of the TypedDicts in effects.py, which cannot be read at runtime (at least not in py3.8)
_REQUIRED_EFFECT_FIELDS: Final = {
    EffectType.SET_QUERY: ("query",),
    EffectType.RENDER_RESULTS: ("results",),
    EffectType.OPEN: ("path",),
    EffectType.LEGACY_COPY: ("text",),
    EffectType.LEGACY_RUN_SCRIPT: ("args",),
    EffectType.LEGACY_RUN_MANY: ("effects",),
    EffectType.LEGACY_ACTIVATE_CUSTOM: ("ref", "keep_app_open"),
}
_events = EventBus()


def is_effect_message(value: Any) -> TypeGuard[EffectMessage]:
    if (
        isinstance(value, dict)
        and (effect_type := value.get("type"))
        and isinstance(effect_type, str)
        and effect_type in _VALID_EFFECT_TYPES
    ):
        return all(field in value for field in _REQUIRED_EFFECT_FIELDS.get(effect_type, ()))
    return False


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


def handle(effect_msg: NonRenderEffectMessage, prevent_close: bool = False) -> None:
    """Process non-rendering effects by dispatching to appropriate handlers."""

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

    elif effect_msg["type"] == EffectType.LEGACY_RUN_MANY:
        # Only the deprecated ActionList produces this, and nested renders are dropped because the
        # callers that can render intercept run_many first. Goes away with the v2 extension API,
        # so leave it separate from the current effect paths instead of unifying the two.
        for effect in effect_msg["effects"]:
            if effect["type"] != EffectType.RENDER_RESULTS:
                handle(effect, True)

    if should_close(effect_msg) and not prevent_close:
        _events.emit("app:close_launcher")
