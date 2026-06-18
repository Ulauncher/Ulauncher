"""Typed IPC messages exchanged between Ulauncher and an extension process.

Both processes run the same Ulauncher code (the extension gets it via PYTHONPATH), so these
types are the single source of truth for the wire format on both ends. They follow the
discriminated-union style of `ulauncher.internals.effects`: each message is a TypedDict tagged
by its `type`, and the unions below let the type checker narrow on it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, TypedDict, Union

if TYPE_CHECKING:
    from typing_extensions import NotRequired

    from ulauncher.internals.effects import EffectMessage
    from ulauncher.internals.result import Result


class InputTriggerEvent(TypedDict):
    type: Literal["event:input_trigger"]
    args: list[Any]  # [argument, trigger_id]


class LaunchTriggerEvent(TypedDict):
    type: Literal["event:launch_trigger"]
    args: list[Any]  # [trigger_id]


class ResultActivationEvent(TypedDict):
    type: Literal["event:result_activation"]
    args: list[Any]  # [action_id, Result]


class LegacyActivateCustomEvent(TypedDict):
    type: Literal["event:legacy_activate_custom"]
    ref: int
    keep_app_open: bool


class UpdatePreferencesEvent(TypedDict):
    type: Literal["event:update_preferences"]
    args: list[Any]  # [id, new_value, old_value]


class LegacyPreferencesLoadEvent(TypedDict):
    type: Literal["event:legacy_preferences_load"]
    args: list[Any]  # [preferences]


class UnloadEvent(TypedDict):
    type: Literal["event:unload"]


# Events that expect a reply routed back to the caller's callback.
Request = Union[
    InputTriggerEvent,
    LaunchTriggerEvent,
    ResultActivationEvent,
    LegacyActivateCustomEvent,
]

# Fire-and-forget events with no reply.
Notification = Union[UpdatePreferencesEvent, LegacyPreferencesLoadEvent, UnloadEvent]

Event = Union[Request, Notification]


class Response(TypedDict):
    """A response an extension sends for a Request.

    `keep_app_open` carries the originating action's close behavior back. The request_id that
    correlates the response to its pending callback travels in the transport envelope, not here.
    """

    keep_app_open: NotRequired[bool]
    effect: EffectMessage | list[Result]
