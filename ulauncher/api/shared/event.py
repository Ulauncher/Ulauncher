from pickle import loads, dumps


class BaseEvent:

    def __eq__(self, other):
        return dumps(self) == dumps(other)

    def __ne__(self, other):
        return dumps(self) != dumps(other)


# pylint: disable=too-few-public-methods
class RegisterEvent(BaseEvent):
    """
    This event is triggered when a new extension connects to the server socket.
    """
    def __init__(self, extension_id):
        self.extension_id = extension_id


class KeywordQueryEvent(BaseEvent):
    """
    Is triggered when user enters query that starts with your keyword + Space

    :param ~ulauncher.modes.Query.Query query:
    :param ~ulauncher.modes.extensions.ExtensionPreferences preferences:
    """

    def __init__(self, query, preferences):
        self.query = query
        self.preferences = preferences

    def get_keyword_id(self):
        """
        :rtype: str
        :returns: the keyword id, as specified in the manifest
        """
        keyword = self.query.get_keyword()
        keyword_id = ""

        for pref in self.preferences.get_items():
            if pref['type'] == "keyword" and pref['value'] == keyword:
                keyword_id = pref['id']
        return keyword_id

    def get_keyword(self):
        """
        :rtype: str
        :returns: the keyword the user entered (you likely want the get_keyword_id() instead)
        """
        return self.query.get_keyword()

    def get_query(self):
        """
        :rtype: :class:`~ulauncher.modes.Query.Query`
        """
        return self.query

    def get_argument(self):
        """
        :rtype: str
        :returns: None if arguments were not specified
        """
        return self.query.get_argument()


# pylint: disable=too-few-public-methods
class ItemEnterEvent(BaseEvent):
    """
    Is triggered when selected item has action of type :class:`~ulauncher.api.shared.action.ExtensionCustomAction`
    Whatever data you've passed to action will be available in in this class using method :meth:`get_data`

    :param str data:
    """

    def __init__(self, data):
        self._data = data

    def get_data(self):
        """
        :returns: whatever object you have passed to :class:`~ulauncher.api.shared.action.ExtensionCustomAction`
        """
        return loads(self._data)


class SystemExitEvent(BaseEvent):
    """
    Is triggered when extension is about to be terminated.

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

    def __init__(self, id, old_value, new_value):
        self.id = id
        self.old_value = old_value
        self.new_value = new_value


class PreferencesEvent(BaseEvent):
    """
    Is triggered on start

    :param dict preferences:
    """

    preferences = None

    def __init__(self, preferences):
        self.preferences = preferences
