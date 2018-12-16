from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction


# pylint: disable=too-few-public-methods
class TestOpenUrlAction:

    def test_run(self, mocker):
        webbrowser = mocker.patch('ulauncher.api.shared.action.OpenUrlAction.webbrowser')
        OpenUrlAction('url').run()
        webbrowser.open_new_tab.assert_called_with('url')
