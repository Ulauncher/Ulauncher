from __future__ import annotations

from pathlib import Path

from ulauncher.modes.shortcuts.shortcuts import Shortcut, Shortcuts


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


class TestShortcuts:
    def test_dict_values_are_coerced_on_set(self) -> None:
        shortcuts = Shortcuts({"first": {"name": "first"}})
        shortcuts["second"] = {"name": "second"}

        assert isinstance(shortcuts["first"], Shortcut)
        assert shortcuts["first"].name == "first"
        assert isinstance(shortcuts["second"], Shortcut)
        assert shortcuts["second"].name == "second"

    def test_accepts_shortcut_instances(self) -> None:
        shortcut = Shortcut(name="Test")
        shortcuts = Shortcuts({"test": shortcut})

        assert shortcuts["test"] == shortcut

    def test_none_value_deletes_key(self) -> None:
        shortcuts = Shortcuts()
        shortcuts["custom"] = {"keyword": "c"}

        shortcuts["custom"] = None

        assert "custom" not in shortcuts
