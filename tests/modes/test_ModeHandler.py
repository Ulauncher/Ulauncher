from unittest import mock

import pytest

from ulauncher.modes.BaseMode import BaseMode
from ulauncher.modes.ModeHandler import ModeHandler


class TestSearch:
    @pytest.fixture
    def search_mode(self):
        return mock.create_autospec(BaseMode)

    @pytest.fixture
    def search(self, search_mode):
        return ModeHandler([search_mode])

    def test_on_query_change__on_query_change__is_called_on_search_mode(self, search, search_mode):
        search_mode.is_enabled.return_value = True
        search.on_query_change("test")
        search_mode.on_query_change.assert_called_once_with("test")
