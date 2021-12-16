import subprocess
from ulauncher.api.shared.action.BaseAction import BaseAction


class OpenAction(BaseAction):
    """
    Run platform specific command to open a file path or URL

    :param str item: file path or URL
    """

    def __init__(self, item):
        self.item = item

    def keep_app_open(self):
        return False

    def run(self):
        subprocess.Popen(['xdg-open', self.item])
