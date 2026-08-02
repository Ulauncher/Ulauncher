from __future__ import annotations

from pathlib import Path
from typing import Any

from ulauncher.modes.shortcuts.shortcuts import Shortcut


class TestShortcut:
    def test_coerces_legacy_icon_path(self) -> None:
        shortcut = Shortcut(icon="/media/google-search-icon.svg")

        assert shortcut.icon == "/icons/google-search.svg"

    def test_folds_user_icon_path(self) -> None:
        shortcut = Shortcut(icon=str(Path.home() / "icons" / "custom.png"))

        assert shortcut.icon == "~/icons/custom.png"

    def test_converts_legacy_float_timestamp(self) -> None:
        # Shortcut.__setitem__ coerces this to int, so the declared field type is narrower than the input.
        legacy: dict[str, Any] = {"added": 123.5}
        shortcut = Shortcut(**legacy)

        assert shortcut.added == 123
