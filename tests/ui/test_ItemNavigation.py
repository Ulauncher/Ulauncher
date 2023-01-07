from unittest import mock
import pytest
from ulauncher.ui.ItemNavigation import ItemNavigation


class TestItemNavigation:
    @pytest.fixture
    def items(self):
        return [mock.MagicMock() for _ in range(5)]

    @pytest.fixture
    def nav(self, items):
        return ItemNavigation(items)

    def test_select_is_called(self, nav, items):
        nav.select(1)
        assert nav.selected == 1
        items[1].select.assert_called_once_with()

    def test_select_and_deselect_is_called(self, nav, items):
        nav.select(1)
        nav.select(5)
        items[1].deselect.assert_called_once_with()
        items[0].select.assert_called_once_with()
        assert nav.selected == 0, "First element is not selected"

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

    def test_go_down_from_2nd(self, nav, items):
        nav.select(2)
        nav.go_down()
        items[3].select.assert_called_once_with()

    def test_go_down_from_last(self, nav, items):
        nav.select(4)
        nav.go_down()
        items[0].select.assert_called_once_with()

    def test_enter_by_index(self, nav, items):
        nav.enter("test", 3)
        items[3].result.on_enter.assert_called_with("test")

    def test_enter_no_index(self, nav, items):
        nav.select(2)
        selected_result = items[2].result
        assert nav.enter("test") is (not selected_result.on_enter.return_value.keep_app_open.return_value)
        selected_result.on_enter.return_value.run.assert_called_with()

    def test_enter__alternative(self, nav, items):
        nav.select(2)
        selected_result = items[2].result
        assert nav.enter("test", alt=True) is (not selected_result.on_alt_enter.return_value.keep_app_open.return_value)
        selected_result.on_alt_enter.return_value.run.assert_called_with()
