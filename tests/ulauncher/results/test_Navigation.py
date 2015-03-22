import pytest
import mock
from ulauncher.results.Navigation import Navigation
from ulauncher.results.ResultItem import ResultItem


class TestNavigation(object):

    @pytest.fixture
    def items(self):
        return map(lambda _: mock.create_autospec(ResultItem), range(5))

    @pytest.fixture
    def nav(self, items):
        return Navigation(items)

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

    def test_enter_in_selected(self, nav, items):
        nav.select(4)
        nav.enter()
        items[4].enter.assert_called_once_with()

    def test_enter_by_index(self, nav, items):
        nav.enter(3)
        items[3].enter.assert_called_once_with()

    def test_enter_in_non_existing(self, nav):
        with pytest.raises(IndexError):
            nav.enter(13)
