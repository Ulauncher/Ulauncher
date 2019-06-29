import os
from time import sleep
from random import randint

from ulauncher.api.shared.action.RunScriptAction import RunScriptAction


# pylint: disable=too-few-public-methods
class TestRunScriptAction:

    def test_run(self):
        test_file = '/tmp/ulauncher_test_%s' % randint(1, 111111)
        args = 'hello world'
        RunScriptAction('echo $1 $2 > %s' % test_file, args).run()
        sleep(0.1)
        with open(test_file, 'r') as f:
            assert f.read() == '%s\n' % args
        os.remove(test_file)
