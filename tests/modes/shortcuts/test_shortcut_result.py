import pytest

from ulauncher.internals.query import Query
from ulauncher.modes.shortcuts.shortcut_result import ShortcutResult


class TestShortcutResult:
    @pytest.fixture(autouse=True)
    def run_shortcut(self, mocker):
        return mocker.patch("ulauncher.modes.shortcuts.shortcut_result.run_shortcut")

    @pytest.fixture
    def result(self):
        return ShortcutResult(keyword="kw", name="name", cmd="https://site/?q=%s", icon="icon_path")

    def test_keyword(self, result):
        assert result.keyword == "kw"

    def test_name(self, result):
        assert result.name == "name"

    def test_icon(self, result):
        assert isinstance(result.icon, str)

    def test_on_activation(self, result, run_shortcut):
        result = result.on_activation(Query("kw", "test"))
        run_shortcut.assert_called_once_with("https://site/?q=%s", "test")
        assert not isinstance(result, str)

    def test_on_activation__default_search(self, result, run_shortcut):
        result.is_default_search = True
        result = result.on_activation(Query(None, "search query"))
        run_shortcut.assert_called_once_with("https://site/?q=%s", "search query")
        assert not isinstance(result, str)

    def test_on_activation__run_without_arguments(self, result, run_shortcut):
        result.run_without_argument = True
        result = result.on_activation(Query("kw", None))
        # it doesn't replace %s if run_without_argument = True
        run_shortcut.assert_called_once_with("https://site/?q=%s", None)
        assert not isinstance(result, str)

    def test_on_activation__run_file(self, run_shortcut):
        result = ShortcutResult(keyword="kw", name="name", cmd="/usr/bin/something/%s", icon="icon_path")
        result.on_activation(Query("kw", "query"))
        # Scripts should support both %s and arguments
        run_shortcut.assert_called_once_with("/usr/bin/something/%s", "query")
