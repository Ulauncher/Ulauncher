import mock
import pytest
from ulauncher.search.DefaultSearchMode import DefaultSearchMode
from ulauncher.ext.actions.ActionList import ActionList


class TestDefaultSearchMode:

    @pytest.fixture
    def search_mode(self):
        return DefaultSearchMode()

    def test_on_query(self, mocker, search_mode):
        query = mock.Mock()
        AppDb = mocker.patch('ulauncher.search.DefaultSearchMode.AppDb')
        Render = mocker.patch('ulauncher.search.DefaultSearchMode.RenderResultListAction')

        assert isinstance(search_mode.on_query(query), ActionList)
        AppDb.get_instance.return_value.find.assert_called_with(query)
        Render.assert_called_with(AppDb.get_instance.return_value.find.return_value)
