from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from ulauncher.internals.query import Query
from ulauncher.internals.result import Result
from ulauncher.modes.file_browser.file_browser_mode import FileBrowserMode


def get_results(mode: FileBrowserMode, query: Query) -> list[Result]:
    """Helper to collect results from callback-based handle_query."""
    results = []
    mode.handle_query(query, lambda r: results.extend(r))
    return results


class MockDirEntry:
    def __init__(self, name: str, atime: int, is_file: bool = True) -> None:
        self.name = name
        self._atime = atime
        self._is_file = is_file

    def is_dir(self) -> bool:
        return not self._is_file

    def is_file(self) -> bool:
        return self._is_file

    def stat(self) -> SimpleNamespace:
        return SimpleNamespace(st_atime=self._atime)


class TestFileBrowserMode:
    @pytest.fixture(autouse=True)
    def scandir(self, mocker: MockerFixture) -> MagicMock:
        sd = mocker.patch("ulauncher.modes.file_browser.file_browser_mode.os.scandir")
        sd.return_value = [
            MockDirEntry("a", 1655837759),
            MockDirEntry("D", 1655839002),
            MockDirEntry("B", 1655839892),
            MockDirEntry("c", 1655837959),
        ]
        return sd

    @pytest.fixture
    def mode(self) -> FileBrowserMode:
        return FileBrowserMode()

    def test_is_enabled(self, mode: FileBrowserMode) -> None:
        assert mode.matches_query_str("~/Downloads")
        assert mode.matches_query_str("~")
        assert mode.matches_query_str("$USER/Videos")
        assert mode.matches_query_str("/usr/bin")
        assert mode.matches_query_str("/")
        assert mode.matches_query_str(" /foo/bar")

        assert not mode.matches_query_str("test")
        assert not mode.matches_query_str("+")
        assert not mode.matches_query_str(" ")

    def test_list_files(self, mode: FileBrowserMode) -> None:
        assert mode.list_files("path") == ["a", "B", "c", "D"]
        assert mode.list_files("path", sort_by_atime=True) == ["B", "D", "c", "a"]

    def test_filter_dot_files(self, mode: FileBrowserMode) -> None:
        assert mode.filter_dot_files(["a", ".b", "c", ".d"]) == ["a", "c"]

    def test_handle_query__path_from_q_exists__dir_listing_rendered(self) -> None:
        query = Query(None, "/tmp/")
        flattened_results = [str(r.path) for r in get_results(FileBrowserMode(), query)]
        assert flattened_results == ["/tmp/B", "/tmp/D", "/tmp/c", "/tmp/a"]

    def test_handle_query__invalid_path__empty_list_rendered(self, mode: FileBrowserMode) -> None:
        query = Query(None, "~~")
        assert get_results(mode, query) == []
