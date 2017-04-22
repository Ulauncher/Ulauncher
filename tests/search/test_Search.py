import pytest
import mock
from ulauncher.search.BaseSearchMode import BaseSearchMode
from ulauncher.search.Search import Search


class TestSearch:

    @pytest.fixture
    def search_mode(self):
        return mock.create_autospec(BaseSearchMode)

    @pytest.fixture
    def search(self, search_mode):
        return Search([search_mode])

    def test_on_query_change__run__is_called(self, search, search_mode):
        search_mode.is_enabled.return_value = True
        search.on_query_change('test')

        search_mode.handle_query.return_value.run.assert_called_once_with()

    def test_on_query_change__on_query_change__is_called_on_search_mode(self, search, search_mode):
        search_mode.is_enabled.return_value = True
        search.on_query_change('test')

        search_mode.on_query_change.assert_called_once_with('test')

    def test_on_key_press_event__run__is_called(self, search, search_mode):
        widget = mock.Mock()
        event = mock.Mock()
        search_mode.is_enabled.return_value = True
        search.on_key_press_event(widget, event, 'test')

        search_mode.handle_key_press_event.return_value.run.assert_called_once_with()
