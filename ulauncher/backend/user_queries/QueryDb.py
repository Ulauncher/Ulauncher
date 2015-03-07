from ulauncher.backend.Db import Db


class QueryDb(Db):

    def put(self, key, value):

        self._records[key] = value

    def find(self, key):

        return self._records.get(key)
