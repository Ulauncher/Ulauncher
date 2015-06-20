from ulauncher.ext.actions.OpenUrlAction import OpenUrlAction


class TestOpenUrlAction:

    def test_run(self, mocker):
        webbrowser = mocker.patch('ulauncher.ext.actions.OpenUrlAction.webbrowser')
        OpenUrlAction('url').run()
        webbrowser.open_new_tab.assert_called_with('url')
