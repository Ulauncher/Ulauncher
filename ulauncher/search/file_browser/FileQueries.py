import os
from time import time, sleep
from typing import Optional
from ulauncher.config import STATE_DIR
from ulauncher.utils.db.KeyValueJsonDb import KeyValueJsonDb
from ulauncher.utils.decorator.run_async import run_async
from ulauncher.utils.decorator.singleton import singleton


class FileQueries(KeyValueJsonDb[str, float]):
    __last_put_time = None  # type: Optional[float]
    __last_save_time = None  # type: Optional[float]

    @classmethod
    @singleton
    def get_instance(cls) -> 'FileQueries':
        browser_cache = os.path.join(STATE_DIR, 'file_browser_queries.json')
        db = cls(browser_cache)
        db.open()
        return db

    def __init__(self, basename: str) -> None:
        super().__init__(basename)
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
        super().put(path, self.__last_put_time)
