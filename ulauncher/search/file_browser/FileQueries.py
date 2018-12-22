import os
from time import time, sleep
from typing import Optional
from ulauncher.config import CACHE_DIR
from ulauncher.util.db.KeyValueDb import KeyValueDb
from ulauncher.util.decorator.run_async import run_async
from ulauncher.util.decorator.singleton import singleton


class FileQueries(KeyValueDb[str, float]):
    __last_put_time = None  # type: Optional[float]
    __last_save_time = None  # type: Optional[float]

    @classmethod
    @singleton
    def get_instance(cls) -> 'FileQueries':
        browser_cache = os.path.join(CACHE_DIR, 'file_browser_queries_v2.db')
        db = cls(browser_cache)
        db.open()
        return db

    def __init__(self, basename: str) -> None:
        super(FileQueries, self).__init__(basename)
        self._init_autosave()

    @run_async(daemon=True)
    def _init_autosave(self) -> None:
        """
        We don't want to trigger file I/O on every insert to the DB,
        so we will commit changes asynchronously every 20 sec
        """
        while True:
            if self.__last_save_time is None or self.__last_put_time is None or \
                    self.__last_save_time < self.__last_put_time:
                self.commit()
                self.__last_save_time = time()
            sleep(20)

    def save_query(self, path: str) -> None:
        self.__last_put_time = time()
        super(FileQueries, self).put(path, self.__last_put_time)
