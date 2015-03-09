import os
import pytest
import mock
from ulauncher.backend.apps.AppDb import AppDb


class TestAppDb(object):

    @pytest.fixture
    def app_db(self):
        return AppDb('test')

    @pytest.fixture
    def db_with_data(self, app_db):
        app_db.put('john.desktop', {'name': 'john', 'description': 'test',
                   'desktop_file': 'john.desktop', 'icon': 'icon'})
        app_db.put('james.desktop', {'name': 'james', 'description': 'test',
                   'desktop_file': 'james.desktop', 'icon': 'icon'})
        app_db.put('o.jody.desktop', {'name': 'o.jody', 'description': 'test',
                   'desktop_file': 'o.jdy.desktop', 'icon': 'icon'})
        app_db.put('sandy.desktop', {'name': 'sandy', 'description': 'test',
                   'desktop_file': 'sandy.desktop', 'icon': 'icon'})
        app_db.put('sane.desktop', {'name': 'sane', 'description': 'test',
                   'desktop_file': 'jane.desktop', 'icon': 'icon'})
        return app_db

    @pytest.fixture(autouse=True)
    def get_app_icon_pixbuf(self, mocker):
        return mocker.patch('ulauncher.backend.apps.AppDb.get_app_icon_pixbuf')

    def test_put_app(self, app_db, get_app_icon_pixbuf, mocker):
        app = mock.MagicMock()
        put = mocker.patch.object(app_db, 'put')

        app_db.put_app(app)

        put.assert_called_with(app.get_name.return_value, pytest.DictHasValus({
            "desktop_file": app.get_filename.return_value,
            "name": app.get_name.return_value,
            "description": app.get_description.return_value,
            "icon": get_app_icon_pixbuf.return_value
        }))

    def test_find_max_results(self, db_with_data):
        """It returns no more than limit"""

        assert len(db_with_data.find('j', limit=3)) == 3
        assert len(db_with_data.find('j', limit=2)) == 2

    def test_find_filters_by_min_score(self, db_with_data):
        """It returns matches only if score > min_score"""

        len(db_with_data.find('jo', min_score=50)) == 2
        len(db_with_data.find('jo', min_score=92)) == 0
