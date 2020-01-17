import pytest

from ulauncher.search.apps.AppIconCache import AppIconCache


class TestAppIconCache:

    @pytest.fixture
    def app_icon_cache(self):
        return AppIconCache()

    @pytest.fixture(autouse=True)
    def get_icon_size(self, mocker):
        get_icon_size = mocker.patch('ulauncher.search.apps.AppIconCache.AppResultItem.get_icon_size')
        get_icon_size.return_value = 40
        return get_icon_size

    @pytest.fixture(autouse=True)
    def get_app_icon_pixbuf(self, mocker):
        return mocker.patch('ulauncher.search.apps.AppIconCache.get_app_icon_pixbuf')

    @pytest.fixture
    def cache_with_data(self, app_icon_cache):
        app_icon_cache.add_icon('/foo/calc.desktop', 'calc-icon', 'calc-icon-name')
        app_icon_cache.add_icon('/foo/writer.desktop', 'writer-icon', 'writer-icon-name')
        return app_icon_cache

    def test_remove_icon__icon_exists__returns_none(self, cache_with_data):
        cache_with_data.remove_icon('/foo/calc.desktop')
        assert not cache_with_data.get_pixbuf('/foo/calc.desktop')

    def test_remove_icon__does_not_exist__does_not_throw(self, cache_with_data):
        cache_with_data.remove_icon('/foo/bar.desktop')

    def test_get_pixbuf__call_two_times__uses_cache(self, cache_with_data, get_app_icon_pixbuf):
        cache_with_data.get_pixbuf('/foo/calc.desktop')
        cache_with_data.get_pixbuf('/foo/calc.desktop')
        assert get_app_icon_pixbuf.call_count == 1

    def test_get_pixbuf__call_two_times__does_not_use_cache(self, cache_with_data, get_app_icon_pixbuf, get_icon_size):
        cache_with_data.get_pixbuf('/foo/calc.desktop')
        get_icon_size.return_value = 20
        cache_with_data.get_pixbuf('/foo/calc.desktop')
        assert get_app_icon_pixbuf.call_count == 2

    def test_get_pixbuf__cache_miss__calls_get_app_icon(self, cache_with_data, get_app_icon_pixbuf):
        cache_with_data.get_pixbuf('/foo/calc.desktop')
        get_app_icon_pixbuf.assert_called_with('calc-icon', 40, 'calc-icon-name')
