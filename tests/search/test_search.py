import pytest
import mock
from ulauncher.ext.SearchMode import SearchMode
from ulauncher.search import start_search


@pytest.fixture
def default_search_mode(mocker):
    return mocker.patch('ulauncher.search.default_search_mode')


def test_start_search_uses_custom_mode(default_search_mode):
    query = 'chrome'
    search_mode = mock.create_autospec(SearchMode)
    search_mode.is_enabled.return_value = True
    start_search(query, [search_mode])
    search_mode.is_enabled.assert_called_with(query)
    search_mode.on_query.assert_called_with(query)
    search_mode.on_query.return_value.run_all.assert_called_with()
    assert not default_search_mode.on_query.called


def test_start_search_uses_default_mode(default_search_mode):
    query = 'chrome'
    search_mode = mock.create_autospec(SearchMode)
    search_mode.is_enabled.return_value = False
    start_search(query, [search_mode])
    search_mode.is_enabled.assert_called_with(query)
    assert not search_mode.on_query.called
    default_search_mode.on_query.assert_called_with(query)
    default_search_mode.on_query.return_value.run_all.assert_called_with()
