import os
from operator import itemgetter
from itertools import islice

from ulauncher.helpers import singleton, force_unicode
from ulauncher.utils.KeyValueDb import KeyValueDb
from ulauncher.config import CACHE_DIR


class AppStatDb(KeyValueDb):
    """
    AppStatDb manages app launch statistics
    """

    @classmethod
    @singleton
    def get_instance(cls):
        return cls(os.path.join(CACHE_DIR, 'app_stat_db.db')).open()

    def inc_count(self, path):
        count = self._records.get(path, 0)
        self._records[path] = count + 1

    def get_most_frequent(self, limit=5):
        """
        Returns most frequent apps

        :param int limit: limit
        :param ResultList result_list:
        :return ResultList:
        """
        # import here to avoid circular deps.
        from .AppResultItem import AppResultItem
        from .AppDb import AppDb
        app_db = AppDb.get_instance()

        return [AppResultItem(i) for i in islice(
                filter(None,
                       map(lambda r: app_db.get_by_path(r[0]),
                           sorted(self._records.iteritems(),
                                  key=itemgetter(1),
                                  reverse=True))),
                0, limit)]
