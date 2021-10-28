import os
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
        return cls(os.path.join(DATA_DIR, 'app_stat_v3.db')).open()

    def inc_count(self, app_id):
        count = self._records.get(app_id, 0)
        self._records[app_id] = count + 1

    def get_most_frequent(self, limit=5):
        """
        Returns most frequent apps

        TODO: rename to `get_most_recent` and update method to remove old apps

        :param int limit: limit
        :rtype: class:`ResultList`
        """

        top_results = sorted(self._records.items(), key=lambda rec: rec[1], reverse=True)[:limit]
        return [rec[0] for rec in top_results]
