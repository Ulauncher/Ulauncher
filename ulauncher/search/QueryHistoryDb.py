import os
from ulauncher.config import DATA_DIR
from ulauncher.utils.db.KeyValueDb import KeyValueDb
from ulauncher.utils.decorator.singleton import singleton


class QueryHistoryDb(KeyValueDb):

    @classmethod
    @singleton
    def get_instance(cls):
        db = cls(os.path.join(DATA_DIR, 'query_history.db'))
        db.open()
        return db

    def save_query(self, query: str, item_name: str):
        """
        Saves "query -> item_name" mapping to history
        so later ulauncher can autoselect item with that name
        if the same query is entered
        """
        if not query:
            # ignore cases when item is selected from the list of frequent apps
            return

        self.put(query, item_name)
        self.commit()
