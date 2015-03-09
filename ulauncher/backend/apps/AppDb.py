from fuzzywuzzy import process
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
        return self.put(record['name'], record)

    def find(self, name, limit=9, min_score=0):
        """
        :param str name: name to search for
        :param int limit: max number of results
        :param int min_score: min score for search results [0..100]
        """
        return map(lambda i: i[0],
                   process.extractBests(name,
                                        self.get_records().values(),
                                        processor=lambda i: i['name'],
                                        limit=limit,
                                        score_cutoff=min_score))
