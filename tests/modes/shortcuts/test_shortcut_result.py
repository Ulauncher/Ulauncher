import pytest

from ulauncher.modes.shortcuts.shortcut_result import ShortcutResult


class TestShortcutResult:
    @pytest.fixture
    def result(self) -> ShortcutResult:
        return ShortcutResult(keyword="kw", name="name", cmd="https://site/?q=%s", icon="icon_path")

    def test_keyword(self, result: ShortcutResult) -> None:
        assert result.keyword == "kw"

    def test_name(self, result: ShortcutResult) -> None:
        assert result.name == "name"

    def test_icon(self, result: ShortcutResult) -> None:
        assert isinstance(result.icon, str)
