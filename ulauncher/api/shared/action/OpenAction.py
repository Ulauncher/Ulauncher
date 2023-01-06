from ulauncher.api.shared.action.BaseAction import BaseAction
from ulauncher.utils.launch_detached import launch_detached


class OpenAction(BaseAction):
    """
    Run platform specific command to open a file path or URL
    """

    def __init__(self, item: str):
        self.item = item

    def run(self):
        launch_detached(["xdg-open", self.item])
