import pytest

from ulauncher.internals.query import Query
from ulauncher.modes.shortcuts.shortcut_result import ShortcutResult


class TestShortcutResult:
    @pytest.fixture(autouse=True)
    def open_action(self, mocker):
        return mocker.patch("ulauncher.modes.shortcuts.shortcut_result.actions.open")

    @pytest.fixture(autouse=True)
    def run_script(self, mocker):
        return mocker.patch("ulauncher.modes.shortcuts.shortcut_result.run_script")

    @pytest.fixture
    def result(self):
        return ShortcutResult(keyword="kw", name="name", cmd="https://site/?q=%s", icon="icon_path")

    def test_keyword(self, result):
        assert result.keyword == "kw"

    def test_name(self, result):
        assert result.name == "name"

    def test_get_description(self, result):
        assert result.get_description(Query("kw test")) == "https://site/?q=test"
        assert result.get_description(Query("keyword test")) == "https://site/?q=..."
        assert result.get_description(Query("goo")) == "https://site/?q=..."

    def test_icon(self, result):
        assert isinstance(result.icon, str)

    def test_on_activation(self, result, open_action):
        result = result.on_activation(Query("kw test"))
        open_action.assert_called_once_with("https://site/?q=test")
        assert not isinstance(result, str)

    def test_on_activation__default_search(self, result, open_action):
        result.is_default_search = True
        result = result.on_activation(Query("search query"))
        open_action.assert_called_once_with("https://site/?q=search query")
        assert not isinstance(result, str)

    def test_on_activation__run_without_arguments(self, result, open_action):
        result.run_without_argument = True
        result = result.on_activation(Query("kw"))
        # it doesn't replace %s if run_without_argument = True
        open_action.assert_called_once_with("https://site/?q=%s")
        assert not isinstance(result, str)

    def test_on_activation__misspelled_kw(self, result, open_action):
        assert result.on_activation(Query("keyword query")) == "kw "
        assert not open_action.called

    def test_on_activation__run_file(self, run_script):
        result = ShortcutResult(keyword="kw", name="name", cmd="/usr/bin/something/%s", icon="icon_path")
        result.on_activation(Query("kw query"))
        # Scripts should support both %s and arguments
        run_script.assert_called_once_with("/usr/bin/something/query", "query")
