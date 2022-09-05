from ulauncher.api.shared.action.BaseAction import BaseAction
from ulauncher.utils.trigger_action import trigger_action


class SetUserQueryAction(BaseAction):
    """
    Changes query string to a new one
    """

    keep_app_open = True

    def __init__(self, new_query: str):
        self.new_query = new_query

    def run(self):
        trigger_action("set_query", [self.new_query])
