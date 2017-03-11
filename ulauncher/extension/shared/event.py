from pickle import loads, dumps


class BaseEvent(object):

    def __eq__(self, other):
        return dumps(self) == dumps(other)

    def __ne__(self, other):
        return dumps(self) != dumps(other)


class KeywordQueryEvent(BaseEvent):

    def __init__(self, query):
        self.query = query

    def get_keyword(self):
        return self.query.get_keyword()

    def get_query(self):
        return self.query

    def get_argument(self):
        """
        Returns None if arguments were not specified
        """
        return self.query.get_argument()


class ItemEnterEvent(BaseEvent):

    def __init__(self, data):
        """
        data - string
        """
        self._data = data

    def get_data(self):
        return loads(self._data)


class SystemExitEvent(BaseEvent):
    pass


class PreferencesUpdateEvent(BaseEvent):

    key = None
    old_value = None
    new_value = None

    def __init__(self, key, old_value, new_value):
        self.key = key
        self.old_value = old_value
        self.new_value = new_value


class PreferencesEvent(BaseEvent):

    preferences = None

    def __init__(self, preferences):
        self.preferences = preferences
