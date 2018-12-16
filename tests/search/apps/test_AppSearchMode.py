import mock
import pytest
from ulauncher.search.apps.AppSearchMode import AppSearchMode


class TestAppSearchMode:

    @pytest.fixture(autouse=True)
    def Render(self, mocker):
        return mocker.patch('ulauncher.search.apps.AppSearchMode.RenderResultListAction')

    @pytest.fixture(autouse=True)
    def app_db(self, mocker):
        return mocker.patch('ulauncher.search.apps.AppSearchMode.AppDb.get_instance').return_value

    @pytest.fixture
    def search_modes(self):
        return []

    @pytest.fixture
    def mode(self, search_modes):
        return AppSearchMode(search_modes)

    def test_handle_query__result__is_Render_result_value(self, mode, Render):
        query = mock.Mock()
        assert mode.handle_query(query) == Render.return_value

    def test_handle_query__RenderResultListAction__is_called(self, mode, app_db, Render):
        query = mock.Mock()
        app_db.find.return_value = [mock.Mock() for i in range(4)]
        mode.handle_query(query)
        Render.assert_called_once_with(app_db.find.return_value)

    def test_handle_query__result_list__is_extended(self, mode, app_db, search_modes):
        query = mock.Mock()
        other_search_mode = mock.Mock()
        other_search_mode.get_searchable_items.return_value = []
        search_modes.append(other_search_mode)
        app_db.find.return_value = [mock.Mock() for i in range(4)]

        mode.handle_query(query)

        other_search_mode.get_searchable_items.assert_called_once_with()

    def test_handle_query__no_results_for_query__returns_default_items(self, mode, app_db, Render, search_modes):
        query = mock.Mock()
        app_db.find.return_value = []
        result_item = mock.Mock()
        other_search_mode = mock.Mock()
        other_search_mode.get_searchable_items.return_value = []
        other_search_mode.get_default_items.return_value = [result_item]
        search_modes.append(other_search_mode)

        mode.handle_query(query)

        Render.assert_called_once_with([result_item])
