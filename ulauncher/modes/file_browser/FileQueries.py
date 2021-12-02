import os
from time import time
from ulauncher.config import STATE_DIR
from ulauncher.utils.db.KeyValueJsonDb import KeyValueJsonDb
from ulauncher.utils.decorator.singleton import singleton


class FileQueries(KeyValueJsonDb[str, float]):
    @classmethod
    @singleton
    def get_instance(cls) -> 'FileQueries':
        db = cls(os.path.join(STATE_DIR, 'file_browser_queries.json'))
        db.open()
        return db

    def save_query(self, path: str) -> None:
        self.put(path, time())
        self.commit()
