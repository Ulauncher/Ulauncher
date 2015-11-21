import os
import pytest
import mock
from ulauncher.search.apps.AppDb import AppDb
from collections import Iterable


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

    @pytest.fixture(autouse=True)
    def force_unicode(self, mocker):
        force_unicode = mocker.patch('ulauncher.search.apps.AppDb.force_unicode')
        force_unicode.side_effect = lambda x: x

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

    def test_find_returns_sorted_results(self, db_with_data, mocker):
        SortedResultList = mocker.patch('ulauncher.search.apps.AppDb.SortedResultList')
        result_list = SortedResultList.return_value
        AppResultItem = mocker.patch('ulauncher.search.apps.AppDb.AppResultItem')

        assert db_with_data.find('bro') is result_list
        result_list.append.assert_called_with(AppResultItem.return_value)
        SortedResultList.assert_called_with('bro', min_score=mock.ANY, limit=9)

        for rec in db_with_data.get_records().values():
            AppResultItem.assert_any_call(rec)

    def test_find_empty_query(self, db_with_data, mocker):
        assert isinstance(db_with_data.find(''), Iterable)
