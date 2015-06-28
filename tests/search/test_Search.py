import pytest
import mock
from ulauncher.ext.SearchMode import SearchMode
from ulauncher.search import Search


class TestSearch:

    @pytest.fixture
    def default_mode(self):
        return mock.create_autospec(SearchMode)

    @pytest.fixture
    def another_mode(self):
        return mock.create_autospec(SearchMode)

    @pytest.fixture
    def search(self, default_mode, another_mode):
        return Search(default_mode, [another_mode])

    def test_choose_search_mode(self, search, default_mode, another_mode):
        another_mode.is_enabled.return_value = False
        assert search.choose_search_mode('q') == default_mode
        another_mode.is_enabled.return_value = True
        assert search.choose_search_mode('q') == another_mode

    def test_start(self, search, another_mode):
        search.start('q')
        another_mode.on_query.assert_called_with('q')
        another_mode.on_query.return_value.run_all.assert_called_with()

    def test_on_key_press_event(self, search, another_mode):
        widget = mock.Mock()
        event = mock.Mock()
        search.on_key_press_event(widget, event, 'q')
        another_mode.on_key_press_event.assert_called_with(widget, event, 'q')
