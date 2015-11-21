import os
import re
import sqlite3
from time import time

from ulauncher.helpers import singleton, split_camel_case, force_unicode
from ulauncher.config import CACHE_DIR


class FileDb(object):

    COMMIT_INTERVAL = 4  # run db.commit() not more than once every `COMMIT_INTERVAL` seconds

    # regular expressions
    _word_sep = re.compile('([-_+\.])')
    _ext_parser = re.compile('(^| )\.(?P<ext>\w[\w\d]*)( |$)', re.I)  # parse extension in a query string

    _path = None
    _conn = None  # sqlite3.Connection
    _last_commit_at = 0

    @classmethod
    @singleton
    def get_instance(cls):
        return cls(os.path.join(CACHE_DIR, 'file_v1.sqlite'))

    def __init__(self, path):
        self._path = path

    def open(self):
        createDbScheme = self._path == ':memory:' or not os.path.exists(self._path)
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        if createDbScheme:
            self._create_table()
        return self

    def commit(self, force=False):
        now = time()
        if force or now - self._last_commit_at > self.COMMIT_INTERVAL:
            self._last_commit_at = now
            self._conn.commit()

    def _create_table(self):
        self._conn.executescript('''
            CREATE TABLE files (path VARCHAR PRIMARY KEY, ext, keywords);
            CREATE VIRTUAL TABLE files_fts USING fts4(content="files", ext, keywords, prefix="1,2,3");

            CREATE TRIGGER files_bu BEFORE UPDATE ON files BEGIN
              DELETE FROM files_fts WHERE docid=old.rowid;
            END;
            CREATE TRIGGER files_bd BEFORE DELETE ON files BEGIN
              DELETE FROM files_fts WHERE docid=old.rowid;
            END;

            CREATE TRIGGER files_au AFTER UPDATE ON files BEGIN
              INSERT INTO files_fts (docid, ext, keywords) VALUES (new.rowid, new.ext, new.keywords);
            END;
            CREATE TRIGGER files_ai AFTER INSERT ON files BEGIN
              INSERT INTO files_fts (docid, ext, keywords) VALUES (new.rowid, new.ext, new.keywords);
            END;''')

    def put_path(self, path):
        filename = os.path.basename(path)
        record = {
            "path": force_unicode(path),
            "ext": force_unicode(os.path.splitext(path)[1].lower()[1:]),
            "keywords": force_unicode(self._tokenize_filename(filename))
        }

        self._conn.execute('''INSERT OR IGNORE INTO files (path, ext, keywords)
                           VALUES (:path, :ext, :keywords)''', record)
        self.commit()

    def _tokenize_filename(self, filename):
        # split camelCased words
        return filename + ' ' + self._word_sep.sub(' ', split_camel_case(filename, sep=' '))

    def get_files(self):
        for rec in self._conn.execute('SELECT path FROM files'):
            yield rec[0]

    def remove_path(self, path):
        """
        Remove path from the DB
        """
        self._conn.execute('DELETE FROM files WHERE path = ?', (path,))
        self.commit()

    def find(self, query, limit=20):
        sql = '''SELECT path FROM files WHERE rowid in (SELECT docid FROM files_fts
                 WHERE files_fts MATCH ? limit ?);'''
        query = self._optimize_query(query)
        for rec in self._conn.execute(sql, (force_unicode(query), limit)):
            if os.path.exists(rec[0]):
                yield rec[0]

    def _optimize_query(self, query):
        """
        fileName-something .png  ->  ext:png* file* name* something*
        """
        new_query = ''

        try:
            ext = self._ext_parser.search(query).group('ext')
        except Exception:
            ext = None

        if ext:
            new_query += 'ext:%s ' % ext
            # remove extension from original query
            query = query.replace('.%s' % ext, '')

        new_query += self._word_sep.sub(' ', query.strip())
        new_query = '* '.join(new_query.split(' ')) + '*'

        return new_query
