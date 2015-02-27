import os
import pytest
import mock
from ulauncher.backend.apps.AppDb import AppDb


class TestAppDb(object):

    @pytest.fixture
    def db_name(self, tmpdir):
        return os.path.join(str(tmpdir), 'testdb')

    @pytest.fixture
    def app_db(self, db_name):
        return AppDb(db_name).open()

    @pytest.fixture
    def db_with_data(self, app_db):
        app_db.put({'name': 'john', 'description': 'test', 'desktop_file': 'john.desktop', 'icon': 'icon'})
        app_db.put({'name': 'james', 'description': 'test', 'desktop_file': 'james.desktop', 'icon': 'icon'})
        app_db.put({'name': 'o.jody', 'description': 'test', 'desktop_file': 'o.jdy.desktop', 'icon': 'icon'})
        app_db.put({'name': 'sandy', 'description': 'test', 'desktop_file': 'sandy.desktop', 'icon': 'icon'})
        app_db.put({'name': 'sane', 'description': 'test', 'desktop_file': 'jane.desktop', 'icon': 'icon'})
        return app_db

    def test_open_raises_ioerror(self):
        """It raises IOError if 'name' is a directory"""

        with pytest.raises(IOError):
            AppDb('/tmp').open()

    def test_commit(self, db_name):
        """It saves changes to disk"""

        db = AppDb(db_name).open()
        db.put({"desktop_file": "test_commit", "name": "hello"})
        db.commit()

        db = AppDb(db_name).open()
        db.find('hello')[0]['desktop_file'] == 'test_commit'

    def test_find_max_results(self, db_with_data):
        """It returns no more than limit"""

        assert len(db_with_data.find('j', limit=3)) == 3
        assert len(db_with_data.find('j', limit=2)) == 2

    def test_find_filters_by_min_score(self, db_with_data):
        """It returns matches only if score > min_score"""

        len(db_with_data.find('jo', min_score=50)) == 2
        len(db_with_data.find('jo', min_score=92)) == 0

    def test_remove(self, app_db):
        app_db.put({'name': 'john', 'description': 'test', 'desktop_file': 'john.desktop', 'icon': 'icon'})
        app_db.put({'name': 'james', 'description': 'test', 'desktop_file': 'james.desktop', 'icon': 'icon'})
        assert app_db.records.get('james')
        app_db.remove('james')
        assert not app_db.records.get('james')
