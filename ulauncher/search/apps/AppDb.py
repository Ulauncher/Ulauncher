import os
import re
import sqlite3
import logging

from ulauncher.search.SortedList import SortedList
from ulauncher.utils.decorator.singleton import singleton
from ulauncher.search.apps.AppResultItem import AppResultItem
from ulauncher.search.apps.AppIconCache import AppIconCache

logger = logging.getLogger(__name__)


class AppDb:

    @classmethod
    @singleton
    def get_instance(cls):
        return cls(':memory:', AppIconCache.get_instance()).open()  # in-memory SqLite DB

    def __init__(self, path: str, app_icon_cache: AppIconCache):
        self._path = path
        self._app_icon_cache = app_icon_cache
        self._conn = None

    def open(self):
        create_db_scheme = self._path == ':memory:' or not os.path.exists(self._path)
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        if create_db_scheme:
            self._create_table()
        return self

    def get_cursor(self):
        return self._conn.cursor()

    # pylint: disable=unused-argument
    def commit(self, force=False):
        self._conn.commit()

    def _create_table(self):
        self._conn.executescript('''
            CREATE TABLE app_db (
              name VARCHAR,
              desktop_file VARCHAR,
              desktop_file_short VARCHAR,
              description VARCHAR,
              search_name VARCHAR,
              PRIMARY KEY (desktop_file_short)
            );
            CREATE INDEX desktop_file_idx ON app_db (desktop_file);
        ''')

    def _row_to_rec(self, row):
        """
        :param sqlite3.Row row:
        """
        return {
            'desktop_file': row['desktop_file'],
            'desktop_file_short': row['desktop_file_short'],
            'name': row['name'],
            'description': row['description'],
            'search_name': row['search_name'],
            'icon': self._app_icon_cache.get_pixbuf(row['desktop_file']),
        }

    def put_app(self, app):
        """
        :param Gio.DesktopAppInfo app:
        """
        name = app.get_string('X-GNOME-FullName') or app.get_name()
        exec_name = app.get_string('Exec') or ''
        record = {
            "desktop_file": app.get_filename(),
            "desktop_file_short": os.path.basename(app.get_filename()),
            "description": app.get_description() or '',
            "name": name,
            "search_name": search_name(name, exec_name)
        }
        self._app_icon_cache.add_icon(record['desktop_file'], app.get_icon(), app.get_string('Icon'))

        query = '''INSERT OR REPLACE INTO app_db (name, desktop_file, desktop_file_short, description, search_name)
                   VALUES (:name, :desktop_file, :desktop_file_short, :description, :search_name)'''
        try:
            self._conn.execute(query, record)
            self.commit()
        # pylint: disable=broad-except
        except Exception as e:
            logger.exception('Exception %s for query: %s. Record: %s', e, query, record)

    def get_by_name(self, name):
        query = 'SELECT * FROM app_db where name = ? COLLATE NOCASE'
        try:
            collection = self._conn.execute(query, (name,))
        except Exception as e:
            logger.exception('Exception %s for query: %s. Name: %s', e, query, name)
            raise

        row = collection.fetchone()
        if row:
            return self._row_to_rec(row)

        return None

    def get_by_path(self, desktop_file):
        query = 'SELECT * FROM app_db where desktop_file = ?'
        try:
            collection = self._conn.execute(query, (desktop_file,))
        except Exception as e:
            logger.exception('Exception %s for query: %s. Path: %s', e, query, desktop_file)
            raise

        row = collection.fetchone()
        if row:
            return self._row_to_rec(row)

        return None

    def remove_by_path(self, desktop_file):
        """
        :param str desktop_file: path to a desktop file
        """
        query = 'DELETE FROM app_db WHERE desktop_file = ?'
        try:
            self._conn.execute(query, (desktop_file,))
            self.commit()
        except Exception as e:
            logger.exception('Exception %s for query: %s. Path: %s', e, query, desktop_file)
            raise

        self._app_icon_cache.remove_icon(desktop_file)

    def get_records(self):
        for row in self._conn.execute('SELECT * FROM app_db'):
            yield self._row_to_rec(row)

    def find(self, query, result_list=None):
        """
        :param str query: query to search for
        :param ResultList result_list:
        :rtype: :class:`ResultList`
        """

        result_list = result_list or SortedList(query, min_score=50, limit=9)

        if not query:
            return result_list

        for rec in self.get_records():
            result_list.append(AppResultItem(rec))

        return result_list


def search_name(name, exec_name):
    """
    Returns string that will be used for search
    We want to make sure app can be searchable by its exec_name
    """
    if not exec_name:
        return name

    # drop env vars
    exec_name = ' '.join([p for p in exec_name.split(' ') if p != 'env' and '=' not in p])

    # drop "/usr/bin/"
    match = re.match(r'^(\/.+\/)?([-\w\.]+)([^\w\/]|$)', exec_name.lower(), re.I)
    if not match:
        return name

    exec_name = match.group(2)
    exec_name_split = set(exec_name.split('-'))
    name_split = set(name.lower().split(' '))
    common_words = exec_name_split & name_split

    if common_words:
        return name

    return '%s %s' % (name, exec_name)
