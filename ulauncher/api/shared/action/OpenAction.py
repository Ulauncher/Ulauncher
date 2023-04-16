from ulauncher.api.shared.action.BaseAction import BaseAction
from ulauncher.utils.trigger_action import trigger_action


class OpenAction(BaseAction):
    """
    Run platform specific command to open a file path or URL
    """

    def __init__(self, item: str):
        self.item = item

    def run(self):
        trigger_action("open", [self.item])
