import mock
import pytest
from ulauncher.ext.actions.ActionList import ActionList
from ulauncher.ext.actions.BaseAction import BaseAction


class TestActionList:

    def create_action(self, keep_app_open):
        action = mock.create_autospec(BaseAction)
        action.keep_app_open.return_value = keep_app_open
        return action

    def test_keep_app_open(self):
        l = ActionList((self.create_action(False), self.create_action(True), self.create_action(False)))
        assert l.keep_app_open()
        l = ActionList((self.create_action(False), self.create_action(False)))
        assert not l.keep_app_open()

    def test_run_all(self):
        l = ActionList((self.create_action(False), self.create_action(True), self.create_action(False)))
        l.run_all()

        l[0].run.assert_called_with()
        l[1].run.assert_called_with()
        l[2].run.assert_called_with()
