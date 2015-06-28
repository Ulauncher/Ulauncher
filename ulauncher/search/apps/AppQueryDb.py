import os
from ulauncher.helpers import singleton
from ulauncher.config import CACHE_DIR
from ulauncher.utils.KeyValueDb import KeyValueDb


class AppQueryDb(KeyValueDb):

    @classmethod
    @singleton
    def get_instance(cls):
        db = cls(os.path.join(CACHE_DIR, 'app_queries.db'))
        db.open()
        return db
