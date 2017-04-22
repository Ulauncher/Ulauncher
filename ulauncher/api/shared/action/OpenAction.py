import sys
import os
import subprocess
from .BaseAction import BaseAction


class OpenAction(BaseAction):
    """
    Run platform specific command to open either file, directory or URL
    """

    def __init__(self, filename):
        """
        file name or path
        """
        self.filename = filename

    def keep_app_open(self):
        return False

    def run(self):
        if sys.platform.startswith('darwin'):
            subprocess.call(('open', self.filename))
        elif os.name == 'nt':
            os.startfile(self.filename)
        elif os.name == 'posix':
            subprocess.call(('xdg-open', self.filename))
