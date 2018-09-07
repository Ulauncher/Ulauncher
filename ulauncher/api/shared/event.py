from pickle import loads, dumps


class BaseEvent(object):

    def __eq__(self, other):
        return dumps(self) == dumps(other)

    def __ne__(self, other):
        return dumps(self) != dumps(other)


class KeywordQueryEvent(BaseEvent):
    """
    Is triggered when user enters query that starts with your keyword + Space

    :param ~ulauncher.search.Query.Query query:
    """

    def __init__(self, query):
        self.query = query

    def get_keyword(self):
        """
        :rtype: str
        """
        return self.query.get_keyword()

    def get_query(self):
        """
        :rtype: :class:`~ulauncher.search.Query.Query`
        """
        return self.query

    def get_argument(self):
        """
        :rtype: str
        :returns: None if arguments were not specified
        """
        return self.query.get_argument()


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
    pass


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
