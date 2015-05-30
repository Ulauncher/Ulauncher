import pytest
import mock
from ulauncher.ui.ItemNavigation import ItemNavigation
from ulauncher.ui.ResultItemWidget import ResultItemWidget


class TestItemNavigation(object):

    @pytest.fixture
    def items(self):
        return map(lambda _: mock.create_autospec(ResultItemWidget), range(5))

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

    def test_enter_by_index(self, nav, items, mocker):
        action_on_enter = mocker.patch.object(nav, "_action_on_enter")
        nav.enter('test', 3)
        action_on_enter.assert_called_once_with(items[3], 'test')

    def test_enter_no_index(self, nav, items, mocker):
        action_on_enter = mocker.patch.object(nav, "_action_on_enter")
        nav.select(2)
        nav.enter('test')
        action_on_enter.assert_called_once_with(items[2], 'test')

    def test_action_on_enter(self, nav, items):
        item = items[0]
        item.get_keyword.return_value = 'query'

        assert nav._action_on_enter(item, 'query arg1') is item.on_enter.return_value.keep_app_open.return_value
        item.on_enter.assert_called_with(argument='arg1')
        item.on_enter.return_value.run_all.assert_called_with()

    def test_action_on_enter_wrong_keyword(self, nav, items, mocker):
        SetUserQueryAction = mocker.patch('ulauncher.ui.ItemNavigation.SetUserQueryAction')
        item = items[0]
        item.get_keyword.return_value = 'query'

        assert nav._action_on_enter(item, 'qery arg1') is item.on_enter.return_value.keep_app_open.return_value
        item.on_enter.assert_called_with(argument=None)
        item.on_enter.return_value.run_all.assert_called_with()
        item.on_enter.return_value.add.assert_called_with(SetUserQueryAction.return_value)
        SetUserQueryAction.assert_called_with('query ')

    def test_action_on_enter_no_args(self, nav, items, mocker):
        SetUserQueryAction = mocker.patch('ulauncher.ui.ItemNavigation.SetUserQueryAction')
        item = items[0]
        item.get_keyword.return_value = 'query'

        assert nav._action_on_enter(item, 'qery') is item.on_enter.return_value.keep_app_open.return_value
        item.on_enter.assert_called_with(argument=None)
        item.on_enter.return_value.run_all.assert_called_with()
        item.on_enter.return_value.add.assert_called_with(SetUserQueryAction.return_value)
        SetUserQueryAction.assert_called_with('query ')
