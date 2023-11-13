from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from ulauncher.config import PATHS
from ulauncher.utils.json_conf import JsonConf

logger = logging.getLogger()
DEFAULT_THEME = "light"
CSS_RESET = """
* {
  color: inherit;
  font-size: inherit;
  font-family: inherit;
  font-style: inherit;
  font-variant: inherit;
  font-weight: inherit;
  text-shadow: inherit;
  -icon-shadow: inherit;
  background-color: initial;
  box-shadow: initial;
  margin: initial;
  padding: initial;
  border-color: initial;
  border-style: initial;
  border-width: initial;
  border-radius: initial;
  outline-color: initial;
  outline-style: initial;
  outline-width: initial;
  outline-offset: initial;
  background-clip: initial;
  background-origin: initial;
  background-size: initial;
  background-position: initial;
  background-repeat: initial;
  background-image: initial;
  transition-property: initial;
  transition-duration: initial;
  transition-timing-function: initial;
  transition-delay: initial;
}
"""


def get_themes():
    """
    Gets a dict with the theme name as the key and theme as the value
    """
    themes = {}

    css_theme_paths = [
        *Path(PATHS.SYSTEM_THEMES).glob("*.css"),
        *Path(PATHS.USER_THEMES).glob("*.css"),
    ]

    all_themes = [Theme(name=p.stem, base_path=str(p.parent)) for p in css_theme_paths]

    # legacy Ulauncher manifest themes
    for manifest_path in Path(PATHS.USER_THEMES).glob("**/manifest.json"):
        data = json.loads(manifest_path.read_text())
        if data.get("extend_theme", "") is None:
            del data["extend_theme"]
        all_themes.append(LegacyTheme(data, base_path=str(manifest_path.parent)))

    for theme in all_themes:
        try:
            theme.validate()
            if themes.get(theme.name):
                logger.warning("Duplicate theme name '%s'", theme.name)
            else:
                themes[theme.name] = theme
        except Exception as e:
            logger.warning(
                "Ignoring invalid or broken theme '%s' in '%s' (%s): %s",
                theme.name,
                theme.base_path,
                type(e).__name__,
                e,
            )

    return themes


class Theme(JsonConf):
    name = ""
    base_path = ""  # Runtime value, should not be stored

    def get_css_path(self):
        return Path(self.base_path, f"{self.name}.css")

    def get_css(self):
        css = self.get_css_path().read_text()
        # Convert relative links to absolute
        return CSS_RESET + re.sub(r"(?<=url\([\"\'])(\./)?(?!\/)", f"{self.base_path}/", css)

    def validate(self):
        try:
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


class LegacyTheme(Theme):
    css_file = ""
    extend_theme = ""
    matched_text_hl_colors: dict[str, str] = {}

    def get_css_path(self):
        # `css_file_gtk_3.20+` is the only supported one if both are specified, otherwise css_file is
        return Path(self.base_path, self.get("css_file_gtk_3.20+", self.css_file))

    def get_css(self):
        css = self.get_css_path().read_text()
        # Convert relative links to absolute
        css = CSS_RESET + re.sub(r"(?<=url\([\"\'])(\./)?(?!\/)", f"{self.base_path}/", css)
        highlight_color = self.matched_text_hl_colors.get("when_not_selected")
        selected_highlight_color = self.matched_text_hl_colors.get("when_selected")
        if self.extend_theme:
            parent_theme = LegacyTheme.load(self.extend_theme)
            if parent_theme.get_css_path().is_file():
                css = f"{parent_theme.get_css()}\n\n{css}"
            else:
                logger.error('Cannot extend theme "%s". It does not exist', self.extend_theme)
        if highlight_color:
            css += f".item-highlight {{ color: {highlight_color} }}"
        if selected_highlight_color:
            css += f".selected.item-box .item-highlight {{ color: {selected_highlight_color} }}"
        return css

    def validate(self):
        try:
            for prop in ["name", "css_file"]:
                assert self.get(prop), f'"{prop}" is empty'
            assert self.get_css_path().is_file(), f"{self.get_css_path()} is not a file"
        except AssertionError as e:
            raise ThemeError(e) from e


class ThemeError(Exception):
    pass
