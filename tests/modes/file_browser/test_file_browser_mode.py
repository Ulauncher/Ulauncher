from types import SimpleNamespace

import pytest

from ulauncher.internals.query import Query
from ulauncher.modes.file_browser.file_browser_mode import FileBrowserMode


class MockDirEntry:
    def __init__(self, name, atime, is_file=True):
        self.name = name
        self._atime = atime
        self._is_file = is_file

    def is_dir(self):
        return not self._is_file

    def is_file(self):
        return self._is_file

    def stat(self):
        return SimpleNamespace(st_atime=self._atime)


class TestFileBrowserMode:
    @pytest.fixture(autouse=True)
    def scandir(self, mocker):
        sd = mocker.patch("ulauncher.modes.file_browser.file_browser_mode.os.scandir")
        sd.return_value = [
            MockDirEntry("a", 1655837759),
            MockDirEntry("D", 1655839002),
            MockDirEntry("B", 1655839892),
            MockDirEntry("c", 1655837959),
        ]
        return sd

    @pytest.fixture
    def mode(self):
        return FileBrowserMode()

    def test_is_enabled(self, mode):
        assert mode.parse_query_str("~/Downloads")
        assert mode.parse_query_str("~")
        assert mode.parse_query_str("$USER/Videos")
        assert mode.parse_query_str("/usr/bin")
        assert mode.parse_query_str("/")
        assert mode.parse_query_str(" /foo/bar")

        assert not mode.parse_query_str("test")
        assert not mode.parse_query_str("+")
        assert not mode.parse_query_str(" ")

    def test_list_files(self, mode):
        assert mode.list_files("path") == ["a", "B", "c", "D"]
        assert mode.list_files("path", sort_by_atime=True) == ["B", "D", "c", "a"]

    def test_filter_dot_files(self, mode):
        assert mode.filter_dot_files(["a", ".b", "c", ".d"]) == ["a", "c"]

    def test_handle_query__path_from_q_exists__dir_listing_rendered(self):
        query = Query(None, "/tmp/")
        flattened_results = [str(r.path) for r in FileBrowserMode().handle_query(query)]
        assert flattened_results == ["/tmp/B", "/tmp/D", "/tmp/c", "/tmp/a"]

    def test_handle_query__invalid_path__empty_list_rendered(self, mode):
        query = Query(None, "~~")
        assert mode.handle_query(query) == []
