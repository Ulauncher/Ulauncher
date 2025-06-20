from ulauncher.modes.file_browser.file_browser_result import FileBrowserResult


class TestFileBrowserResult:
    def test_get_name(self) -> None:
        assert FileBrowserResult("/tmp/dir").name == "dir"

    def test_icon(self) -> None:
        assert isinstance(FileBrowserResult("/tmp/").icon, str)
