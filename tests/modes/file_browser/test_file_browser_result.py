from ulauncher.modes.file_browser.file_browser_result import FileBrowserResult


class TestFileBrowserResult:
    def test_get_name(self):
        assert FileBrowserResult("/tmp/dir").name == "dir"

    def test_icon(self):
        assert isinstance(FileBrowserResult("/tmp/").icon, str)
