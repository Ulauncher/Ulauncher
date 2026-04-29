from __future__ import annotations

from pathlib import Path

from ulauncher.modes.shortcuts.shortcuts import Shortcut


class TestShortcut:
    def test_coerces_legacy_icon_path(self) -> None:
        shortcut = Shortcut(icon="/media/google-search-icon.svg")

        assert shortcut.icon == "/icons/google-search.svg"

    def test_folds_user_icon_path(self) -> None:
        shortcut = Shortcut(icon=str(Path.home() / "icons" / "custom.png"))

        assert shortcut.icon == "~/icons/custom.png"

    def test_converts_legacy_float_timestamp(self) -> None:
        shortcut = Shortcut(added=123.5)

        assert shortcut.added == 123
