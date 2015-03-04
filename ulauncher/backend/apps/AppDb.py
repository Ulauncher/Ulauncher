from fuzzywuzzy import process

from ulauncher.backend.Db import Db


class AppDb(Db):

    def put(self, rec):
        """
        :param str rec['name']:
        :param str rec['description']:
        :param str rec['desktop_file']:
        :param str rec['icon']:
        """
        self._records[rec['name']] = rec

    def find(self, name, limit=9, min_score=0):
        """
        :param str name: name to search for
        :param int limit: max number of results
        :param int min_score: min score for search results [0..100]
        """
        return map(lambda i: i[0],
                   process.extractBests(name, self._records.values(),
                                        processor=lambda i: i['name'], limit=limit, score_cutoff=min_score))
