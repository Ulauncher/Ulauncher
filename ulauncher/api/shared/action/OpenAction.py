import subprocess
from ulauncher.api.shared.action.BaseAction import BaseAction


class OpenAction(BaseAction):
    """
    Run platform specific command to open either file or directory

    :param str path: file or dir path
    """

    def __init__(self, path):
        self.path = path

    def keep_app_open(self):
        return False

    def run(self):
        subprocess.Popen(['xdg-open', self.path])
