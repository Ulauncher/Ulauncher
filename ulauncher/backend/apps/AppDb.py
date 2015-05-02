from Levenshtein import ratio
from ulauncher.backend.Db import Db
from .icon_loader import get_app_icon_pixbuf


class AppDb(Db):

    def put_app(self, app):
        """
        :param Gio.DesktopAppInfo app:
        """
        record = {
            "desktop_file": app.get_filename(),
            "name": app.get_name(),
            "description": app.get_description(),
            "icon": get_app_icon_pixbuf(app)
        }
        # use name as a key in order to skip duplicates
        return self.put(record['name'], record)

    def remove_by_path(self, desktop_file):
        """
        :desktop_file str: path to a desktop file
        """
        records = self.get_records()
        for key in records.iterkeys():
            if records[key].get('desktop_file') == desktop_file:
                del records[key]
                return True

        return False

    def _calculate_score(self, query, rec_name):
        """
        Calculate score for each word from rec_name separately
        and then take the best one
        """
        rec_name = rec_name.lower()

        # improve score (max. by 50%) for queries that occur in a record name:
        # formula: 50 - (<index of substr>/<name length>)
        extra_score = 0
        if query in rec_name:
            index = rec_name.index(query)
            extra_score += 50 - (index * 50. / len(rec_name))

            # add extra 10% to a score, if record starts with a query
            extra_score += 10 if index == 0 else 0

        best_score = 0
        for word in rec_name.split(' '):
            score = ratio(query, word) * 100 + extra_score

            if score > best_score:
                best_score = score

        return best_score

    def find(self, name, limit=9, min_score=0):
        """
        :param str name: name to search for
        :param int limit: max number of results
        :param int min_score: min score for search results [0..100]
        :return list: [{<record dict>}, ...]
        """

        if not name:
            return []

        name = name.lower()
        matches = []  # (score, record) tuples

        for rec in self.get_records().values():
            score = self._calculate_score(name, rec['name'])

            if score >= min_score:
                matches.append((score, rec))

        # sort and return only first `limit` number of items
        return map(lambda (_, r): r, sorted(matches, reverse=True)[:limit])
