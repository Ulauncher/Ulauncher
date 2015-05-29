import os
import pytest
import mock
from ulauncher.search.apps.AppDb import AppDb


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
        app_db.put('jane.desktop', {'name': 'jane', 'description': 'test',
                   'desktop_file': 'jane.desktop', 'icon': 'icon'})
        app_db.put('libre.calc', {'name': 'LibreOffice Calc', 'description': 'test',
                   'desktop_file': 'libre.calc', 'icon': 'icon'})
        app_db.put('calc', {'name': 'Calc', 'description': 'test',
                   'desktop_file': 'calc', 'icon': 'icon'})
        app_db.put('Guake Terminal', {'name': 'Guake Terminal', 'description': 'test',
                   'desktop_file': 'Guake Terminal', 'icon': 'icon'})
        app_db.put('Keyboard', {'name': 'Keyboard', 'description': 'test',
                   'desktop_file': 'Keyboard', 'icon': 'icon'})
        return app_db

    @pytest.fixture(autouse=True)
    def get_app_icon_pixbuf(self, mocker):
        return mocker.patch('ulauncher.search.apps.AppDb.get_app_icon_pixbuf')

    def test_remove_by_path(self, db_with_data):
        assert db_with_data.get_records().get('jane.desktop')
        assert db_with_data.remove_by_path('jane.desktop')
        assert not db_with_data.get_records().get('jane.desktop')

    def test_put_app(self, app_db, get_app_icon_pixbuf, mocker):
        app = mock.MagicMock()
        app.get_string.return_value = None
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

        assert len(db_with_data.find('jo', min_score=50)) == 2
        assert len(db_with_data.find('Jo', min_score=92)) == 1

    def test_find_scrores_higher_items_start_with_query(self, db_with_data):
        results = db_with_data.find('cal', min_score=90)
        assert results[0]['desktop_file'] == 'calc'
        assert results[1]['desktop_file'] == 'libre.calc'

        results = db_with_data.find('ke', min_score=80)
        assert results[0]['desktop_file'] == 'Keyboard'
        assert results[1]['desktop_file'] == 'Guake Terminal'

    def test_find_takes_into_account_spaces_in_names(self, db_with_data):
        results = db_with_data.find('cal', min_score=70)
        assert results[0]['desktop_file'] == 'calc'
        assert results[1]['desktop_file'] == 'libre.calc'
