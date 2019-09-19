import os
from operator import itemgetter
from itertools import islice

from ulauncher.config import DATA_DIR
from ulauncher.utils.db.KeyValueDb import KeyValueDb
from ulauncher.utils.decorator.singleton import singleton


class AppStatDb(KeyValueDb):
    """
    AppStatDb manages app launch statistics
    """

    @classmethod
    @singleton
    def get_instance(cls):
        return cls(os.path.join(DATA_DIR, 'app_stat_v2.db')).open()

    def inc_count(self, path):
        count = self._records.get(path, 0)
        self._records[path] = count + 1

    def get_most_frequent(self, limit=5):
        """
        Returns most frequent apps

        TODO: rename to `get_most_recent` and update method to remove old apps

        :param int limit: limit
        :rtype: class:`ResultList`
        """

        # pylint: disable=relative-beyond-top-level
        # import here to avoid circular deps.
        from ulauncher.search.apps.AppResultItem import AppResultItem
        from ulauncher.search.apps.AppDb import AppDb
        app_db = AppDb.get_instance()

        return [AppResultItem(i) for i in islice(
            filter(None,
                   map(lambda r: app_db.get_by_path(r[0]),
                       sorted(self._records.items(),
                              key=itemgetter(1),
                              reverse=True))),
            0, limit)]
