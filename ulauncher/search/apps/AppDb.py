import os
import sqlite3
import logging

from ulauncher.helpers import singleton, force_unicode
from ulauncher.config import CACHE_DIR
from ulauncher.utils.icon_loader import get_app_icon_pixbuf
from ulauncher.result_list.SortedResultList import SortedResultList
from .AppResultItem import AppResultItem

logger = logging.getLogger(__name__)


class AppDb(object):

    @classmethod
    @singleton
    def get_instance(cls):
        return cls(':memory:').open()  # in-memory SqLite DB

    def __init__(self, path):
        self._path = path
        self._icons = {}  # save icons to a local map

    def open(self):
        createDbScheme = self._path == ':memory:' or not os.path.exists(self._path)
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        if createDbScheme:
            self._create_table()
        return self

    def get_cursor(self):
        return self._conn.cursor()

    def commit(self, force=False):
        self._conn.commit()

    def _create_table(self):
        self._conn.executescript('''
            CREATE TABLE app_db (name VARCHAR PRIMARY KEY, desktop_file VARCHAR,
            description VARCHAR);
            CREATE INDEX desktop_file_idx ON app_db (desktop_file);''')

    def _row_to_rec(self, row):
        """
        :row sqlite3.Row:
        """
        return {
            'desktop_file': row['desktop_file'],
            'name': row['name'],
            'description': row['description'],
            'icon': self._icons[row['desktop_file']],
        }

    def get_icons(self):
        return self._icons

    def put_app(self, app):
        """
        :param Gio.DesktopAppInfo app:
        """
        record = {
            "desktop_file": force_unicode(app.get_filename()),
            "name": force_unicode(app.get_string('X-GNOME-FullName') or app.get_name()),
            "description": force_unicode(app.get_description() or ''),
        }
        self._icons[record['desktop_file']] = get_app_icon_pixbuf(app, AppResultItem.ICON_SIZE)

        try:
            query = '''INSERT OR IGNORE INTO app_db (name, desktop_file, description)
                       VALUES (:name, :desktop_file, :description)'''
            self._conn.execute(query, record)
            self.commit()
        except Exception as e:
            logger.exception('Exception %s for query: %s. Record: %s' % (e, query, record))

    def get_by_name(self, name):
        try:
            query = 'SELECT * FROM app_db where name = ? COLLATE NOCASE'
            collection = self._conn.execute(query, (force_unicode(name),))
        except Exception as e:
            logger.exception('Exception %s for query: %s. Name: %s' % (e, query, name))

        row = collection.fetchone()
        if row:
            return self._row_to_rec(row)

    def get_by_path(self, desktop_file):
        try:
            query = 'SELECT * FROM app_db where desktop_file = ?'
            collection = self._conn.execute(query, (force_unicode(desktop_file),))
        except Exception as e:
            logger.exception('Exception %s for query: %s. Path: %s' % (e, query, desktop_file))

        row = collection.fetchone()
        if row:
            return self._row_to_rec(row)

    def remove_by_path(self, desktop_file):
        """
        :desktop_file str: path to a desktop file
        """
        try:
            query = 'DELETE FROM app_db WHERE desktop_file = ?'
            self._conn.execute(query, (force_unicode(desktop_file),))
            self.commit()
        except Exception as e:
            logger.exception('Exception %s for query: %s. Path: %s' % (e, query, desktop_file))

        del self._icons[desktop_file]

    def get_records(self):
        for row in self._conn.execute('SELECT * FROM app_db'):
            yield self._row_to_rec(row)

    def find(self, query, result_list=None):
        """
        :param str query: query to search for
        :param ResultList result_list:
        :return ResultList:
        """

        result_list = result_list or SortedResultList(query, min_score=50, limit=9)

        if not query:
            return result_list

        for rec in self.get_records():
            result_list.append(AppResultItem(rec))

        return result_list
