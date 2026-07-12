# Legacy import path. Definitions live in ulauncher.api.event.
from ulauncher.api.event import (
    BaseEvent,
    EventType,
    ExtensionPreferences,
    ExtensionPreferenceValue,
    InputTriggerEvent,
    LaunchTriggerEvent,
    PreferencesUpdateEvent,
    ResultActivationEvent,
    UnloadEvent,
)
from ulauncher.api.event import (
    LegacyItemEnterEvent as ItemEnterEvent,
)
from ulauncher.api.event import (
    LegacyKeywordQueryEvent as KeywordQueryEvent,
)
from ulauncher.api.event import (
    LegacyPreferencesEvent as PreferencesEvent,
)

# Alias of UnloadEvent for backward compatibility. In v6, please use UnloadEvent (or extension.on_unload) instead
SystemExitEvent = UnloadEvent

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
]
