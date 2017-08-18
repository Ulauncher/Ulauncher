import os
from time import time, sleep
from ulauncher.config import CACHE_DIR
from ulauncher.util.db.KeyValueDb import KeyValueDb
from ulauncher.util.decorator.run_async import run_async
from ulauncher.util.decorator.singleton import singleton


class FileQueries(KeyValueDb):
    __last_put_time = None
    __last_save_time = None

    @classmethod
    @singleton
    def get_instance(cls):
        """
        Issue #151: Migrates the old cache file into one with a corrected filename.
        TODO: Remove once enough users are migrated
        """
        old_browser_cache = os.path.join(CACHE_DIR, 'file_borwser_queries.db')
        browser_cache = os.path.join(CACHE_DIR, 'file_browser_queries.db')
        if os.path.isfile(old_browser_cache):
            os.rename(old_browser_cache, browser_cache)

        db = cls(browser_cache)
        db.open()
        return db

    def __init__(self, basename):
        super(FileQueries, self).__init__(basename)
        self._init_autosave()

    @run_async(daemon=True)
    def _init_autosave(self):
        """
        We don't want to trigger I/O on every insert to the DB,
        so we will commit changes asynchronously every 20 sec
        """
        while True:
            if self.__last_save_time < self.__last_put_time:
                self.commit()
                self.__last_save_time = time()
            sleep(20)

    def put(self, path):
        self.__last_put_time = time()
        super(FileQueries, self).put(path, self.__last_put_time)
