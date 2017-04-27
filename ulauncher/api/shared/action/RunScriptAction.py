import time
import os
import subprocess
import tempfile
from .BaseAction import BaseAction


class RunScriptAction(BaseAction):
    """
    Runs a user script

    :param str script: script content
    :param list args: arguments
    """

    def __init__(self, script, args):
        self.script = script
        self.args = args

    def run(self):
        file = tempfile.NamedTemporaryFile(prefix='ulauncher_RunScript_', delete=False)

        try:
            file.write(self.script)
        except Exception:
            file.close()
            raise
        else:
            file.close()

        try:
            os.chmod(file.name, 0o777)
            subprocess.Popen(["%s %s" % (file.name, self.args)],
                             shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)
            time.sleep(.05)  # wait just a bit, because Popen runs file asynchronously
            os.remove(file.name)
        except Exception:
            os.remove(file.name)
            raise
