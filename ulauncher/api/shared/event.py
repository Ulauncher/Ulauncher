from __future__ import annotations

from typing import Any

from ulauncher.internals.query import Query


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
        self.query = Query.parse_str(query_str)
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


class UnloadEvent(BaseEvent):
    """
    Is triggered when extension is about to be unloaded (terminated).

    Your extension has 300ms to handle this event and shut down properly.
    After that it will be terminated with SIGKILL
    """


class PreferencesUpdateEvent(BaseEvent):
    """
    Is triggered when user updates preference through Preferences window

    :param str id:
    :param str old_value:
    :param str new_value:
    """

    id = None
    old_value = None
    new_value = None

    def __init__(self, args: Any) -> None:
        super().__init__(args)
        self.id, self.new_value, self.old_value = args


class PreferencesEvent(BaseEvent):
    """
    Is triggered on start

    :param dict preferences:
    """

    preferences = None

    def __init__(self, args: list[Any]) -> None:
        super().__init__(args)
        self.preferences = args[0]


# Alias of UnloadEvent for backward compatibility. In v6, please use UnloadEvent (or extension.on_unload) instead
SystemExitEvent = UnloadEvent

events = {
    "event:launch_trigger": LaunchTriggerEvent,
    "event:update_preferences": PreferencesUpdateEvent,
    "event:legacy_preferences_load": PreferencesEvent,
    "event:unload": UnloadEvent,
    "event:input_trigger": InputTriggerEvent,
    "event:activate_custom": ItemEnterEvent,
}
