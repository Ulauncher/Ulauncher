from typing import Any, List

from ulauncher.api.shared.query import Query


class BaseEvent:
    args: List[Any] = []

    def __init__(self, args: List[Any]):
        self.args = args


class LaunchTriggerEvent(BaseEvent):
    """
    When user activates a launch trigger
    """


class InputTriggerEvent(BaseEvent):
    """
    When user activates an input trigger, passing the input
    """


class KeywordQueryEvent(BaseEvent):
    """
    Deprecated older variant of InputTriggerEvent
    """

    def __init__(self, query: str):
        self.query = Query(query)
        super().__init__([self.query])

    def get_keyword(self) -> str:
        """
        :rtype: str
        """
        return self.query.keyword

    def get_query(self) -> Query:
        return self.query

    def get_argument(self) -> str:
        """
        :rtype: str
        :returns: None if arguments were not specified
        """
        return self.query.argument


class ItemEnterEvent(BaseEvent):
    """
    Is triggered when selected item has action of type :class:`~ulauncher.api.shared.action.ExtensionCustomAction`
    Whatever data you've passed to action will be available in in this class using method :meth:`get_data`

    :param str data:
    """

    def get_data(self):
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

    def __init__(self, args):
        super().__init__(args)
        self.id, self.new_value, self.old_value = args


class PreferencesEvent(BaseEvent):
    """
    Is triggered on start

    :param dict preferences:
    """

    preferences = None

    def __init__(self, args):
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
