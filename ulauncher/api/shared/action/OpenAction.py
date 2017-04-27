import sys
import os
import subprocess
from .BaseAction import BaseAction


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
        if sys.platform.startswith('darwin'):
            subprocess.call(('open', self.path))
        elif os.name == 'nt':
            os.startfile(self.path)
        elif os.name == 'posix':
            subprocess.call(('xdg-open', self.path))
