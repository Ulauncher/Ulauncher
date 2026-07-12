# Legacy import path. Real definitions live in ulauncher.api.event.
from ulauncher.api.event import (
    BaseEvent,
    EventType,
    ExtensionPreferences,
    ExtensionPreferenceValue,
    InputTriggerEvent,
    ItemEnterEvent,
    KeywordQueryEvent,
    LaunchTriggerEvent,
    PreferencesEvent,
    PreferencesUpdateEvent,
    ResultActivationEvent,
    SystemExitEvent,
    UnloadEvent,
    events,
)

__all__ = [
    "BaseEvent",
    "EventType",
    "ExtensionPreferenceValue",
    "ExtensionPreferences",
    "InputTriggerEvent",
    "ItemEnterEvent",
    "KeywordQueryEvent",
    "LaunchTriggerEvent",
    "PreferencesEvent",
    "PreferencesUpdateEvent",
    "ResultActivationEvent",
    "SystemExitEvent",
    "UnloadEvent",
    "events",
]
