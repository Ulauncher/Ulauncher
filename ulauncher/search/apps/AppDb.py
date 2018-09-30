import logging
import os
import re
import string

import sqlite3

from ulauncher.search.SortedList import SortedList
from ulauncher.util.decorator.singleton import singleton
from ulauncher.util.image_loader import get_app_icon_pixbuf
from ulauncher.util.string import force_unicode
from .AppResultItem import AppResultItem

logger = logging.getLogger(__name__)


class AppDb(object):

    @classmethod
    @singleton
    def get_instance(cls):
         # in-memory SqLite DB
        return cls(':memory:').open()

    def __init__(self, path):
        self._path = path
        self._icons = {}  # save icons to a local map

    def open(self):
        create_db_scheme = self._path == ':memory:' or not os.path.exists(self._path)
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        if create_db_scheme:
            self._create_table()
        return self

    def get_cursor(self):
        return self._conn.cursor()

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
            'icon': self._icons[row['desktop_file']],
        }

    def get_icons(self):
        return self._icons

    def put_app(self, app):
        """
        :param Gio.DesktopAppInfo app:
        """
        name = force_unicode(app.get_string('X-GNOME-FullName') \
                             or app.get_name() or app.get_generic_name())
        exec_name = force_unicode(app.get_string('Exec') or '')
        keywords = ' '.join([force_unicode(word) for word in app.get_keywords()])
        description = app.get_description() or ''
        record = {
            "desktop_file": force_unicode(app.get_filename()),
            "desktop_file_short": force_unicode(os.path.basename(app.get_filename())),
            "description": force_unicode(app.get_description() or ''),
            "name": name,
            "search_name": search_name(name, exec_name, keywords, description)
        }
        self._icons[record['desktop_file']] = get_app_icon_pixbuf(app, AppResultItem.ICON_SIZE)

        query = '''
            INSERT OR REPLACE INTO app_db (name, desktop_file, desktop_file_short, description, search_name)
                   VALUES (:name, :desktop_file, :desktop_file_short, :description, :search_name)
        '''

        try:
            self._conn.execute(query, record)
            self.commit()
        except Exception as e:
            logger.exception('Exception %s for query: %s. Record: %s' % (e, query, record))

    def get_by_name(self, name):
        query = 'SELECT * FROM app_db where name = ? COLLATE NOCASE'
        try:
            collection = self._conn.execute(query, (force_unicode(name),))
        except Exception as e:
            logger.exception('Exception %s for query: %s. Name: %s' % (e, query, name))
            raise

        row = collection.fetchone()
        if row:
            return self._row_to_rec(row)

    def get_by_path(self, desktop_file):
        query = 'SELECT * FROM app_db where desktop_file = ?'
        try:
            collection = self._conn.execute(query, (force_unicode(desktop_file),))
        except Exception as e:
            logger.exception('Exception %s for query: %s. Path: %s' % (e, query, desktop_file))
            raise

        row = collection.fetchone()
        if row:
            return self._row_to_rec(row)

    def remove_by_path(self, desktop_file):
        """
        :param str desktop_file: path to a desktop file
        """
        query = 'DELETE FROM app_db WHERE desktop_file = ?'
        try:
            self._conn.execute(query, (force_unicode(desktop_file),))
            self.commit()
        except Exception as e:
            logger.exception('Exception %s for query: %s. Path: %s' % (e, query, desktop_file))
            raise

        try:
            del self._icons[desktop_file]
        except KeyError:
            pass

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


def search_name(name, exec_name, keywords, description):

    #   name_words
    # + additional from exec name split
    # + additional from keywords

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    name_words = spaceless_split(name.lower())
    keywords_words = spaceless_split(keywords.lower())

    # strip punctuation
    clean_description = description.translate(None, string.punctuation)
    description_words = [clean_description.lower()]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # remove env vars from exec_name
    clean_exec_name = ' '.join([p for p in spaceless_split(exec_name)
                         if p != 'env' and '=' not in p])
    # remove "/usr/bin/"
    match = re.match(
        r'^(\/.+\/)?([-\w\.]+)([^\w\/]|$)',
        clean_exec_name.lower(),
        re.I
    )
    if match:
        clean_exec_name = match.group(2)
        exec_name_parts = set(clean_exec_name.split('-'))

        # check to see if name words are in exec_name parts
        common_words = exec_name_parts & set(name_words)
        # if there are common words then we do not need the exec_name
        if common_words:
            exec_name_words = []
        else:
            exec_name_words = [clean_exec_name]
    else:
        exec_name_words = []

    # keywords are more precise so attach them first
    search_words = name_words + exec_name_words + keywords_words \
                   + description_words
    search_string = ' '.join(search_words)

    #print ">>>>>"
    #print "  name         :", name
    #print "  search_string:", search_string

    return search_string


def spaceless_split(string):
    return [part for part in string.split(' ') if part != '']
