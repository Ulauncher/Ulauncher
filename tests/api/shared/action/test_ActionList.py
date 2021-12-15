import mock

from ulauncher.api.shared.action.ActionList import ActionList
from ulauncher.api.shared.action.BaseAction import BaseAction


class TestActionList:

    def create_action(self, keep_app_open):
        action = mock.create_autospec(BaseAction)
        action.keep_app_open.return_value = keep_app_open
        return action

    def test_keep_app_open(self):
        list = ActionList((self.create_action(False), self.create_action(True), self.create_action(False)))
        assert list.keep_app_open()
        list = ActionList((self.create_action(False), self.create_action(False)))
        assert not list.keep_app_open()
        list = ActionList()
        assert list.keep_app_open()

    def test_run(self):
        list = ActionList((self.create_action(False), self.create_action(True), self.create_action(False)))
        list.run()

        list[0].run.assert_called_with()
        list[1].run.assert_called_with()
        list[2].run.assert_called_with()
