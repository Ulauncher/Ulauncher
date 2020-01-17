from collections import Iterable
import pytest
import mock
from ulauncher.search.apps.AppDb import AppDb, search_name
from ulauncher.search.apps.AppIconCache import AppIconCache


class TestAppDb:

    @pytest.fixture
    def app_icon_cache(self, mocker):
        get_instance = mocker.patch('ulauncher.search.apps.AppIconCache.AppIconCache.get_instance')
        get_instance.return_value = mock.create_autospec(AppIconCache)
        return get_instance.return_value

    @pytest.fixture
    def app_db(self, app_icon_cache):
        return AppDb(':memory:', app_icon_cache).open()

    @pytest.fixture
    def db_with_data(self, app_db):
        values = [
            {
                'name': 'john',
                'description': 'test',
                'search_name': 'john',
                'desktop_file': '/foo/john.desktop',
                'desktop_file_short': 'john.desktop',
                'icon': 'icon'
            },
            {
                'name': 'james',
                'description': 'test',
                'search_name': 'james',
                'desktop_file': '/foo/james.desktop',
                'desktop_file_short': 'james.desktop',
                'icon': 'icon'
            },
            {
                'name': 'o.jody',
                'description': 'test',
                'search_name': 'o.jody',
                'desktop_file': '/foo/o.jdy.desktop',
                'desktop_file_short': 'o.jdy.desktop',
                'icon': 'icon'
            },
            {
                'name': 'sandy',
                'description': 'test',
                'search_name': 'sandy',
                'desktop_file': '/foo/sandy.desktop',
                'desktop_file_short': 'sandy.desktop',
                'icon': 'icon'
            },
            {
                'name': 'jane',
                'description': 'test',
                'search_name': 'jane',
                'desktop_file': '/foo/jane.desktop',
                'desktop_file_short': 'jane.desktop',
                'icon': 'icon'
            },
            {
                'name': 'LibreOffice Calc',
                'description': 'test',
                'search_name': 'LibreOffice Calc',
                'desktop_file': '/foo/libre.calc',
                'desktop_file_short': 'libre.calc',
                'icon': 'icon'},
            {
                'name': 'Calc',
                'description': 'test',
                'search_name': 'Calc',
                'desktop_file': 'calc',
                'desktop_file_short': 'calc',
                'icon': 'icon'
            },
            {
                'name': 'Guake Terminal',
                'description': 'test',
                'search_name': 'Guake Terminal',
                'desktop_file': 'Guake Terminal',
                'desktop_file_short': 'Guake Terminal',
                'icon': 'icon'
            },
            {
                'name': 'Keyboard',
                'description': 'test',
                'search_name': 'Keyboard',
                'desktop_file': 'Keyboard',
                'desktop_file_short': 'Keyboard',
                'icon': 'icon'
            }
        ]
        app_db.get_cursor().executemany("""
            INSERT INTO app_db (
                name,
                desktop_file,
                desktop_file_short,
                description,
                search_name
            )
            VAlUES (
                :name,
                :desktop_file,
                :desktop_file_short,
                :description,
                :search_name
            )
        """, values)
        return app_db

    def test_remove_by_path(self, db_with_data):
        assert db_with_data.get_by_path('/foo/jane.desktop')
        db_with_data.remove_by_path('/foo/jane.desktop')
        assert not db_with_data.get_by_path('/foo/jane.desktop')

    def test_put_app(self, app_db, app_icon_cache):
        app = mock.MagicMock()
        app.get_filename.return_value = '/foo/file_name_test1'
        app.get_string.return_value = None
        app.get_name.return_value = 'name_test1'
        app.get_description.return_value = 'description_test1'

        app_db.put_app(app)

        assert app_db.get_by_path('/foo/file_name_test1') == {
            'desktop_file': '/foo/file_name_test1',
            'desktop_file_short': 'file_name_test1',
            'name': 'name_test1',
            'description': 'description_test1',
            'search_name': 'name_test1',
            'icon': app_icon_cache.get_pixbuf.return_value
        }

    def test_find_returns_sorted_results(self, db_with_data, mocker):
        SortedList = mocker.patch('ulauncher.search.apps.AppDb.SortedList')
        result_list = SortedList.return_value
        AppResultItem = mocker.patch('ulauncher.search.apps.AppDb.AppResultItem')

        assert db_with_data.find('bro') is result_list
        result_list.append.assert_called_with(AppResultItem.return_value)
        SortedList.assert_called_with('bro', min_score=mock.ANY, limit=9)

        for rec in db_with_data.get_records():
            AppResultItem.assert_any_call(rec)

    def test_find_empty_query(self, db_with_data):
        assert isinstance(db_with_data.find(''), Iterable)

    def test_get_by_name(self, db_with_data, app_icon_cache):
        # also test case insensitive search
        assert db_with_data.get_by_name('JohN') == {
            'name': 'john',
            'description': 'test',
            'desktop_file': '/foo/john.desktop',
            'desktop_file_short': 'john.desktop',
            'icon': app_icon_cache.get_pixbuf.return_value,
            'search_name': 'john'
        }

    def test_get_by_path(self, db_with_data, app_icon_cache):
        # also test case insensitive search
        assert db_with_data.get_by_path('/foo/libre.calc') == {
            'name': 'LibreOffice Calc',
            'description': 'test',
            'desktop_file': '/foo/libre.calc',
            'desktop_file_short': 'libre.calc',
            'icon': app_icon_cache.get_pixbuf.return_value,
            'search_name': 'LibreOffice Calc'
        }


def test_search_name():
    assert search_name('GNU Image Manipulation Program', r'gimp-2.8 %U') == 'GNU Image Manipulation Program gimp-2.8'
    assert search_name('Content Hub Clipboard', r'content-hub-clipboard %U') == 'Content Hub Clipboard'
    assert search_name('Scopes', r'/usr/bin/unity8-dash') == 'Scopes unity8-dash'
    assert search_name('Mouse & Touchpad', r'unity-control-center mouse') == 'Mouse & Touchpad unity-control-center'
    assert search_name('Back Up', r'deja-dup --backup') == 'Back Up deja-dup'
    assert search_name('Calendar', r'gnome-calendar') == 'Calendar'
    assert search_name('Amazon', r'unity-webapps-runner --amazon --app-id=ubuntu-amazon-default') == \
        'Amazon unity-webapps-runner'
    assert search_name('Back Up', r'env VAR1=VAL1 VAR2=VAL2 deja-dup --backup') == 'Back Up deja-dup'
