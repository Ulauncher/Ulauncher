from ulauncher.modes.file_browser.results import FileResult


class TestFileBrowserResult:
    def test_get_name(self) -> None:
        assert FileResult("/fake/dir").name == "dir"

    def test_icon(self) -> None:
        assert isinstance(FileResult("/fake/").icon, str)
