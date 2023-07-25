from ulauncher.api.shared.action.BaseAction import BaseAction
from ulauncher.utils.trigger_action import trigger_action


class CopyToClipboardAction(BaseAction):
    """
    Copy text to the clipboard
    """

    def __init__(self, text: str):
        self.text = text

    def run(self):
        trigger_action({"action": "copy", "value": self.text})
