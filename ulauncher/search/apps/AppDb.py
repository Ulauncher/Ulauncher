import os

from ulauncher.helpers import singleton, force_unicode
from ulauncher.utils.KeyValueDb import KeyValueDb
from ulauncher.utils.icon_loader import get_app_icon_pixbuf
from .AppResultItem import AppResultItem
from ulauncher.search.SortedResultList import SortedResultList
from ulauncher.config import CACHE_DIR


class AppDb(KeyValueDb):

    @classmethod
    @singleton
    def get_instance(cls):
        return cls(os.path.join(CACHE_DIR, 'applist.db'))

    def put_app(self, app):
        """
        :param Gio.DesktopAppInfo app:
        """
        record = {
            "desktop_file": force_unicode(app.get_filename()),
            "name": force_unicode(app.get_string('X-GNOME-FullName') or app.get_name()),
            "description": force_unicode(app.get_description() or ''),
            "icon": get_app_icon_pixbuf(app, AppResultItem.ICON_SIZE)
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

    def find(self, query, result_list=None):
        """
        :param str query: query to search for
        :param ResultList result_list:
        :return ResultList:
        """

        result_list = result_list or SortedResultList(query, min_score=30, limit=9)

        if not query:
            return result_list

        for rec in self.get_records().values():
            result_list.append(AppResultItem(rec))

        return result_list
