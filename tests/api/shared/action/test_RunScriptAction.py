from time import sleep

from ulauncher.api.shared.action.RunScriptAction import RunScriptAction


class TestRunScriptAction:

    def test_get_command__no_args__returns_the_script_only(self):
        assert RunScriptAction('script').get_command('/tmp/script') == '/tmp/script'

    def test_get_command__args__appends_them(self):
        assert RunScriptAction('script', 'hello world').get_command('/tmp/script') == '/tmp/script hello world'

    def test_run__no_args__passes_no_argument(self, tmpdir):
        output_file = str(tmpdir.join('output.txt'))
        RunScriptAction('echo "[$1]" > %s' % output_file).run()
        sleep(0.1)
        with open(output_file, 'r') as f:
            assert f.read() == '[]\n'

    def test_run__args__are_split_into_words_by_the_shell(self, tmpdir):
        output_file = str(tmpdir.join('output.txt'))
        RunScriptAction('echo $1 $2 > %s' % output_file, 'hello world').run()
        sleep(0.1)
        with open(output_file, 'r') as f:
            assert f.read() == 'hello world\n'
