import logging
import json
import re
from pathlib import Path
from typing import Dict

from ulauncher.config import PATHS
from ulauncher.utils.json_data import JsonData, json_data_class

logger = logging.getLogger()
DEFAULT_THEME = "light"


def get_themes():
    """
    Gets a dict with the theme name as the key and theme as the value
    """
    themes = {}
    manifests_paths = [
        *Path(PATHS.SYSTEM_THEMES).glob("**/manifest.json"),
        *Path(PATHS.USER_THEMES).glob("**/manifest.json"),
    ]

    for manifest_path in manifests_paths:
        try:
            theme = Theme(json.loads(manifest_path.read_text()), _path=manifest_path.parent)
            theme.validate()
            themes[theme.name] = theme
        except Exception as e:
            logger.warning("Ignoring invalid or broken theme '%s' (%s): %s", manifest_path, type(e).__name__, e)

    return themes


@json_data_class
class Theme(JsonData):
    manifest_version = ""
    name = ""
    display_name = ""
    css_file = ""
    extend_theme = ""
    matched_text_hl_colors: Dict[str, str] = {}
    _path = ""  # This should not be stored, but we never overwrite these files anyway

    def get_css_path(self):
        # `css_file_gtk_3.20+` is the only supported one if both are specified, otherwise css_file is
        return Path(self._path, self.get("css_file_gtk_3.20+", self.css_file))

    def get_css(self):
        css = self.get_css_path().read_text()
        # Convert relative links to absolute
        css = re.sub(r"(?<=url\([\"\'])(\./)?(?!\/)", f"{self._path}/", css)
        if self.extend_theme:
            parent_theme = Theme.load(self.extend_theme)
            if parent_theme.get_css_path().is_file():
                css = f"{parent_theme.get_css()}\n\n{css}"
            else:
                logger.error('Cannot extend theme "%s". It does not exist', self.extend_theme)
        return css

    def validate(self):
        try:
            assert self.manifest_version == "1", "Supported manifest version is '1'"
            for prop in ["name", "display_name", "matched_text_hl_colors", "css_file"]:
                assert self.get(prop), f'"{prop}" is empty'
            assert self.get_css_path().is_file(), f"{self.get_css_path()} is not a file"
        except AssertionError as e:
            raise ThemeError(e) from e

    @classmethod
    def load(cls, theme_name: str):
        themes = get_themes()
        if theme_name in themes:
            return themes[theme_name]

        logger.warning("Couldn't load theme: '%s'", theme_name)

        if theme_name != DEFAULT_THEME and DEFAULT_THEME in themes:
            return themes[DEFAULT_THEME]

        # Return the first on the list if everything else fails
        return next(iter(themes))


class ThemeError(Exception):
    pass
