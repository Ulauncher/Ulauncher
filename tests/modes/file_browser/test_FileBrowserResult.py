from ulauncher.modes.file_browser.FileBrowserResult import FileBrowserResult


class TestFileBrowserResult:
    def test_get_name(self):
        assert FileBrowserResult('/tmp/dir').get_name() == 'dir'

    def test_icon(self):
        assert isinstance(FileBrowserResult('/tmp/').get_icon(), str)
