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
    Handler for legacy `ExtensionCustomAction`.
    The data object passed to the action will be available using :meth:`get_data`

    :param str data:
    """

    def get_data(self) -> Any:
        """
        :returns: data object passed to `ExtensionCustomAction`
        """
        return self.args[0]


class ResultActivationEvent(BaseEvent):
    """
    Is triggered when user activates a result action.
    Args: [action_id: str, result: Result]

    :param str action_id: The ID of the action that was activated
    :param Result result: The Result object that was activated
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
    LAUNCH_TRIGGER: Final = "event:launch_trigger"
    RESULT_ACTIVATION: Final = "event:result_activation"
    UPDATE_PREFERENCES: Final = "event:update_preferences"
    UNLOAD: Final = "event:unload"
    LEGACY_ACTIVATE_CUSTOM: Final = "event:legacy_activate_custom"
    LEGACY_PREFERENCES_LOAD: Final = "event:legacy_preferences_load"


events = {
    EventType.INPUT_TRIGGER: InputTriggerEvent,
    EventType.LAUNCH_TRIGGER: LaunchTriggerEvent,
    EventType.RESULT_ACTIVATION: ResultActivationEvent,
    EventType.UPDATE_PREFERENCES: PreferencesUpdateEvent,
    EventType.UNLOAD: UnloadEvent,
    EventType.LEGACY_ACTIVATE_CUSTOM: ItemEnterEvent,
    EventType.LEGACY_PREFERENCES_LOAD: PreferencesEvent,
}
