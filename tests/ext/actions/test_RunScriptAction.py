import os
from random import randint
from ulauncher.ext.actions.RunScriptAction import RunScriptAction


class TestRunScriptAction:

    def test_run(self, mocker):
        testFile = '/tmp/ulauncher_test_%s' % randint(1, 111111)
        args = 'hello world'
        RunScriptAction('echo $1 $2 > %s' % testFile, args).run()
        with open(testFile, 'r') as f:
            assert f.read() == '%s\n' % args
        os.remove(testFile)
