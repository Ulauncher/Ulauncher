import os
from ulauncher.config import CACHE_DIR
from ulauncher.util.db.KeyValueDb import KeyValueDb
from ulauncher.util.decorator.singleton import singleton


class AppCacheDb(KeyValueDb):

    @classmethod
    @singleton
    def get_instance(cls):
        db = cls(os.path.join(CACHE_DIR, 'app_cache.db'))
        db.open()
        return db
