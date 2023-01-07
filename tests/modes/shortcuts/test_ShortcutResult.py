import pytest
from ulauncher.modes.shortcuts.ShortcutResult import ShortcutResult
from ulauncher.api.shared.query import Query


class TestShortcutResult:
    @pytest.fixture(autouse=True)
    def OpenAction(self, mocker):
        return mocker.patch("ulauncher.modes.shortcuts.ShortcutResult.OpenAction")

    @pytest.fixture(autouse=True)
    def RunScriptAction(self, mocker):
        return mocker.patch("ulauncher.modes.shortcuts.ShortcutResult.RunScriptAction")

    @pytest.fixture
    def SetUserQueryAction(self, mocker):
        return mocker.patch("ulauncher.modes.shortcuts.ShortcutResult.SetUserQueryAction")

    @pytest.fixture
    def item(self):
        return ShortcutResult(
            "kw", "name", "https://site/?q=%s", "icon_path", is_default_search=True, run_without_argument=False
        )

    def test_keyword(self, item):
        assert item.keyword == "kw"

    def test_name(self, item):
        assert item.name == "name"

    def test_get_description(self, item):
        assert item.get_description(Query("kw test")) == "https://site/?q=test"
        assert item.get_description(Query("keyword test")) == "https://site/?q=..."
        assert item.get_description(Query("goo")) == "https://site/?q=..."

    def test_icon(self, item):
        assert isinstance(item.icon, str)

    def test_on_enter(self, item, OpenAction, SetUserQueryAction):
        item.on_enter(Query("kw test"))
        OpenAction.assert_called_once_with("https://site/?q=test")
        assert not SetUserQueryAction.called

    def test_on_enter__default_search(self, item, OpenAction, SetUserQueryAction):
        item.is_default_search = True
        item.on_enter(Query("search query"))
        OpenAction.assert_called_once_with("https://site/?q=search query")
        assert not SetUserQueryAction.called

    def test_on_enter__run_without_arguments(self, item, OpenAction, SetUserQueryAction):
        item.run_without_argument = True
        item.on_enter(Query("kw"))
        # it doesn't replace %s if run_without_argument = True
        OpenAction.assert_called_once_with("https://site/?q=%s")
        assert not SetUserQueryAction.called

    def test_on_enter__misspelled_kw(self, item, OpenAction, SetUserQueryAction):
        item.on_enter(Query("keyword query"))
        assert not OpenAction.called
        SetUserQueryAction.assert_called_once_with("kw ")

    def test_on_enter__run_file(self, RunScriptAction):
        item = ShortcutResult("kw", "name", "/usr/bin/something/%s", "icon_path")
        item.on_enter(Query("kw query"))
        # Scripts should support both %s and arguments
        RunScriptAction.assert_called_once_with("/usr/bin/something/query", "query")
