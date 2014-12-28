import unittest
import mock
from ulauncher.results.Navigation import Navigation
from ulauncher.results.ResultItem import ResultItem


class TestNavigation(unittest.TestCase):
    def setUp(self):
        self.items = map(lambda _: mock.create_autospec(ResultItem), range(5))
        self.nav = Navigation(self.items)

    def test_select_is_called(self):
        self.nav.select(1)
        self.assertEqual(self.nav.selected, 1)
        self.items[1].select.assert_called_once_with()

    def test_select_and_deselect_is_called(self):
        self.nav.select(1)
        self.nav.select(5)
        self.items[1].deselect.assert_called_once_with()
        self.items[0].select.assert_called_once_with()
        self.assertEqual(self.nav.selected, 0, "First element is not selected")

    def test_go_up_from_start(self):
        self.nav.go_up()
        self.items[4].select.assert_called_once_with()

    def test_go_up_from_1st(self):
        self.nav.select(1)
        self.nav.go_up()
        self.items[0].select.assert_called_once_with()

    def test_go_up_from_last(self):
        self.nav.select(4)
        self.nav.go_up()
        self.items[3].select.assert_called_once_with()

    def test_go_down_from_2nd(self):
        self.nav.select(2)
        self.nav.go_down()
        self.items[3].select.assert_called_once_with()

    def test_go_down_from_last(self):
        self.nav.select(4)
        self.nav.go_down()
        self.items[0].select.assert_called_once_with()

    def test_enter_in_selected(self):
        self.nav.select(4)
        self.nav.enter()
        self.items[4].enter.assert_called_once_with()

    def test_enter_by_index(self):
        self.nav.enter(3)
        self.items[3].enter.assert_called_once_with()

    def test_enter_in_non_existing(self):
        with self.assertRaises(IndexError):
            self.nav.enter(13)
