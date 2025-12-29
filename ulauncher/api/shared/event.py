from __future__ import annotations

from typing import Any, Dict, Final, Union

from ulauncher.internals.query import Query

ExtensionPreferenceValue = Union[str, int, bool]
ExtensionPreferences = Dict[str, ExtensionPreferenceValue]


class BaseEvent:
    args: list[Any] = []

    def __init__(self, args: list[Any]) -> None:
        self.args = args


class LaunchTriggerEvent(BaseEvent):
    """
    When user activates a launch trigger
    """


class InputTriggerEvent(BaseEvent):
    """
    When user activates an input trigger, passing the input
    """


# TODO: Add deprecation warning
class KeywordQueryEvent(BaseEvent):
    """
    Deprecated older variant of InputTriggerEvent
    """

    def __init__(self, query_str: str) -> None:
        argument: str | None = None
        components = query_str.split(" ", 1)
        if len(components) > 1:
            # argument will be an empty string if there is only a space after the keyword (see is_active property)
            argument = components[1]
        self.query = Query(components[0], argument)
        super().__init__([self.query])

    def get_keyword(self) -> str:
        return self.query.keyword or ""

    def get_query(self) -> Query:
        return self.query

    def get_argument(self) -> str:
        return self.query.argument or ""


class ItemEnterEvent(BaseEvent):
    """
    Is triggered when selected item has action of type :class:`~ulauncher.api.shared.action.ExtensionCustomAction`
    Whatever data you've passed to action will be available in in this class using method :meth:`get_data`

    :param str data:
    """

    def get_data(self) -> Any:
        """
        :returns: whatever object you have passed to :class:`~ulauncher.api.shared.action.ExtensionCustomAction`
        """
        return self.args[0]


class ResultActivationEvent(BaseEvent):
    """
    Is triggered when user activates a result action.
    Args: [action_id: str, result_data: dict]

    :param str action_id: The ID of the action that was activated
    :param dict result_data: The result data as a dict
    """


class UnloadEvent(BaseEvent):
    """
    Is triggered when extension is about to be unloaded (terminated).

    Your extension has 300ms to handle this event and shut down properly.
    After that it will be terminated with SIGKILL
    """


class PreferencesUpdateEvent(BaseEvent):
    """
    Is triggered when user updates preference through Preferences window
    """

    id: str
    old_value: ExtensionPreferenceValue
    new_value: ExtensionPreferenceValue

    def __init__(self, args: Any) -> None:
        super().__init__(args)
        self.id, self.new_value, self.old_value = args


class PreferencesEvent(BaseEvent):
    """
    Is triggered on start

    :param dict preferences:
    """

    preferences: ExtensionPreferences

    def __init__(self, args: list[ExtensionPreferences]) -> None:
        super().__init__(args)
        self.preferences = args[0]


# Alias of UnloadEvent for backward compatibility. In v6, please use UnloadEvent (or extension.on_unload) instead
SystemExitEvent = UnloadEvent


class EventType:
    INPUT_TRIGGER: Final = "event:input_trigger"
    ACTIVATE_CUSTOM: Final = "event:activate_custom"
    LAUNCH_TRIGGER: Final = "event:launch_trigger"
    RESULT_ACTIVATION: Final = "event:result_activation"
    UPDATE_PREFERENCES: Final = "event:update_preferences"
    LEGACY_PREFERENCES_LOAD: Final = "event:legacy_preferences_load"
    UNLOAD: Final = "event:unload"


events = {
    EventType.LAUNCH_TRIGGER: LaunchTriggerEvent,
    EventType.UPDATE_PREFERENCES: PreferencesUpdateEvent,
    EventType.LEGACY_PREFERENCES_LOAD: PreferencesEvent,
    EventType.UNLOAD: UnloadEvent,
    EventType.INPUT_TRIGGER: InputTriggerEvent,
    EventType.ACTIVATE_CUSTOM: ItemEnterEvent,
    EventType.RESULT_ACTIVATION: ResultActivationEvent,
}
