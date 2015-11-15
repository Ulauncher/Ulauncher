import os
import pytest
import mock
import time
from ulauncher.search.find.FileDb import FileDb


class TestFileDb(object):

    @pytest.fixture
    def sqlite3(self, mocker):
        return mocker.patch('ulauncher.search.find.FileDb.sqlite3')

    @pytest.fixture(autouse=True)
    def db_conn(self, sqlite3):
        return sqlite3.connect.return_value

    @pytest.fixture
    def file_db(self):
        return FileDb('/tmp/test/path').open()

    def test_open(self, file_db, sqlite3, db_conn):
        sqlite3.connect.assert_called_with('/tmp/test/path', check_same_thread=False)
        db_conn.executescript.assert_called_with(mock.ANY)

    def test_tokenize_filename(self, file_db):
        assert file_db._tokenize_filename('hello-world_dataNew.jpg') ==\
            'hello-world_dataNew.jpg hello world data new jpg'

    def test_optimize_query(self, file_db):
        assert file_db._optimize_query('fileName-something .png') == 'ext:png* fileName* something*'
