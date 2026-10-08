import json

import pytest

from ulauncher.utils.settings import Settings


class TestSettings:
    def test_defaults(self) -> None:
        assert Settings().theme_name == "light"
        assert Settings(theme_name="asdf").theme_name == "asdf"

    def test_recent_apps_defaults_to_the_list_layout(self) -> None:
        settings = Settings()
        assert settings.recent_apps_layout == "list"
        assert settings.recent_apps_grid_columns == 4
        assert settings.recent_apps_grid_labels == "name-and-shortcut"
        assert settings.recent_apps_grid_icon_size == 48

    def test_numeric_settings_accept_hand_edited_strings(self) -> None:
        """settings.json is hand-editable, and Gtk.Adjustment rejects strings outright."""
        settings = Settings()
        settings.update(
            {
                "base_width": "900",
                "max_recent_apps": "8",
                "recent_apps_grid_columns": "4",
                "recent_apps_grid_icon_size": "64",
                "window_shadow": "3",
            }
        )
        assert settings.base_width == 900
        assert settings.max_recent_apps == 8
        assert settings.recent_apps_grid_columns == 4
        assert settings.recent_apps_grid_icon_size == 64
        assert settings.window_shadow == 3

    def test_unusable_numeric_value_falls_back_to_the_default(self) -> None:
        settings = Settings()
        settings.update({"recent_apps_grid_columns": "lots", "recent_apps_grid_icon_size": None})
        assert settings.recent_apps_grid_columns == 4
        assert settings.recent_apps_grid_icon_size == 48

    @pytest.mark.parametrize("literal", ["Infinity", "-Infinity", "1e400", "NaN"])
    def test_infinite_numeric_value_falls_back_instead_of_raising(self, literal: str) -> None:
        """json.loads accepts these; int() rejects an inf with OverflowError, not ValueError."""
        value = json.loads(f'{{"recent_apps_grid_columns": {literal}}}')["recent_apps_grid_columns"]
        settings = Settings()
        settings.update({"recent_apps_grid_columns": value})
        assert settings.recent_apps_grid_columns == 4

    def test_enum_settings_reject_unknown_values(self) -> None:
        """An unknown label mode would render tiles with no labels while the combo shows default."""
        settings = Settings()
        settings.update({"recent_apps_layout": "mosaic", "recent_apps_grid_labels": "bogus"})
        assert settings.recent_apps_layout == "list"
        assert settings.recent_apps_grid_labels == "name-and-shortcut"

    def test_enum_settings_keep_known_values(self) -> None:
        settings = Settings()
        settings.update({"recent_apps_layout": "grid", "recent_apps_grid_labels": "none"})
        assert settings.recent_apps_layout == "grid"
        assert settings.recent_apps_grid_labels == "none"

    def test_numeric_settings_are_clamped_to_their_bounds(self) -> None:
        """A hand-edited column count must not reach the grid: it pads per unused column."""
        settings = Settings()
        settings.update(
            {
                "base_width": 99999,
                "max_recent_apps": 500,
                "recent_apps_grid_columns": "100000",
                "recent_apps_grid_icon_size": 4096,
                "window_shadow": 900,
            }
        )
        assert settings.base_width == 2000
        assert settings.max_recent_apps == 20
        assert settings.recent_apps_grid_columns == 12
        assert settings.recent_apps_grid_icon_size == 128
        assert settings.window_shadow == 25

        settings.update(
            {
                "base_width": 0,
                "max_recent_apps": -5,
                "recent_apps_grid_columns": 0,
                "recent_apps_grid_icon_size": 1,
                "window_shadow": -1,
            }
        )
        assert settings.base_width == 540
        assert settings.max_recent_apps == 0
        assert settings.recent_apps_grid_columns == 1
        assert settings.recent_apps_grid_icon_size == 16
        assert settings.window_shadow == 0

    def test_dash_to_underscore(self) -> None:
        s = Settings()
        assert s.theme_name == "light"
        s.update({"theme-name": "asdf"})
        assert not hasattr(s, "theme-name")
        assert hasattr(s, "theme_name")
        assert s.theme_name == "asdf"
