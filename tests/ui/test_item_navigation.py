from unittest import mock

import pytest

from ulauncher.ui.item_navigation import ItemNavigation


class TestItemNavigation:
    @pytest.fixture
    def items(self):
        return [mock.MagicMock() for _ in range(5)]

    @pytest.fixture
    def nav(self, items):
        return ItemNavigation(items)

    @pytest.fixture(autouse=True)
    def query_history(self, mocker):
        return mocker.patch("ulauncher.ui.item_navigation.query_history")

    @pytest.fixture(autouse=True)
    def json_save(self, mocker):
        return mocker.patch("ulauncher.ui.item_navigation.json_save")

    def test_select_is_called(self, nav, items):
        nav.select(1)
        assert nav.index == 1
        items[1].select.assert_called_once_with()

    def test_select_and_deselect_is_called(self, nav, items):
        nav.select(1)
        nav.select(5)
        items[1].deselect.assert_called_once_with()
        items[0].select.assert_called_once_with()
        assert nav.index == 0, "First element is not selected"

    def test_go_up_from_start(self, nav, items):
        nav.go_up()
        items[4].select.assert_called_once_with()

    def test_go_up_from_1st(self, nav, items):
        nav.select(1)
        nav.go_up()
        items[0].select.assert_called_once_with()

    def test_go_up_from_last(self, nav, items):
        nav.select(4)
        nav.go_up()
        items[3].select.assert_called_once_with()

    def test_go_down_from_second(self, nav, items):
        nav.select(2)
        nav.go_down()
        items[3].select.assert_called_once_with()

    def test_go_down_from_last(self, nav, items):
        nav.select(4)
        nav.go_down()
        items[0].select.assert_called_once_with()

    def test_enter_no_index(self, nav, items):
        nav.select(2)
        selected_result = items[2].result
        nav.activate("test")
        selected_result.on_activation.assert_called_with("test", False)

    def test_enter__alternative(self, nav, items):
        nav.select(2)
        selected_result = items[2].result
        nav.activate("test", True)
        selected_result.on_activation.assert_called_with("test", True)
