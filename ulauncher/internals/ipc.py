"""Typed IPC messages exchanged between Ulauncher and an extension process.

Both processes run the same Ulauncher code (the extension gets it via PYTHONPATH), so these
types are the single source of truth for the wire format on both ends. They follow the
discriminated-union style of `ulauncher.internals.effects`: each message is a TypedDict tagged
by its `type`, and the unions below let the type checker narrow on it.

`args` fields are typed as fixed-length tuples so the type checker can verify their arity and
the type at each position. They are consumed positionally by the receiver (see
`api.extension.Extension.convert_to_baseevent`). On the wire they are JSON arrays, so a parsed
message holds a list there, not a tuple.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Literal, Optional, Tuple, TypedDict, Union

if TYPE_CHECKING:
    from typing_extensions import NotRequired

    from ulauncher.internals.effects import EffectMessage
    from ulauncher.internals.result import Result


class InputTriggerEvent(TypedDict):
    type: Literal["event:input_trigger"]
    args: tuple[str | None, str]  # argument, trigger_id


class LaunchTriggerEvent(TypedDict):
    type: Literal["event:launch_trigger"]
    args: tuple[str]  # trigger_id


class ResultActivationEvent(TypedDict):
    type: Literal["event:result_activation"]
    args: tuple[str, int]  # action_id, result_id


class LegacyActivateCustomEvent(TypedDict):
    type: Literal["event:legacy_activate_custom"]
    ref: int
    keep_app_open: bool


class UpdatePreferencesEvent(TypedDict):
    type: Literal["event:update_preferences"]
    args: tuple[str, Any, Any]  # id, new_value, old_value


class LegacyPreferencesLoadEvent(TypedDict):
    type: Literal["event:legacy_preferences_load"]
    args: tuple[dict[str, Any]]  # preferences


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

# Transport envelope wrapping an event Ulauncher sends to an extension, paired with the request_id
# correlating its response (None for notifications, which expect no reply). Typed as a tuple for
# fixed arity; on the wire it is a JSON array, so a parsed message holds a list here.
EventEnvelope = Tuple[Dict[str, Any], Optional[int]]


class Response(TypedDict):
    """A response an extension sends for a Request.

    `keep_app_open` carries the originating action's close behavior back. The request_id that
    correlates the response to its pending callback travels in the transport envelope, not here.
    """

    keep_app_open: NotRequired[bool]
    effect: EffectMessage | list[Result]


class ResponseMessage(TypedDict):
    name: Literal["response"]
    request_id: int
    response: Response


class ClipboardStoreMessage(TypedDict):
    name: Literal["clipboard_store"]
    text: str


class NotifyMessage(TypedDict):
    name: Literal["notify"]
    body: str
    notification_id: str | None


# Messages an extension sends to Ulauncher, tagged by `name` so the receiver narrows on it.
ExtensionMessage = Union[ResponseMessage, ClipboardStoreMessage, NotifyMessage]
