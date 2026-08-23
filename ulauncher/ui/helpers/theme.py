from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from ulauncher import paths
from ulauncher.data import JsonConf

logger = logging.getLogger(__name__)
DEFAULT_THEME = "light"
CSS_RESET = """
* {
  background: initial;
  border: initial;
  border-radius: initial;
  box-shadow: initial;
  color: inherit;
  font: inherit;
  margin: initial;
  padding: initial;
  text-shadow: inherit;
  transition: initial;
  -icon-shadow: inherit;
  outline: initial;
}
"""


def _load_legacy_theme(manifest_path: Path) -> LegacyTheme | None:
    """Loads a legacy manifest theme, or logs and returns None if the manifest is unusable."""
    try:
        # dict() rejects JSON that isn't an object, KeyError guards keys shadowing a class member.
        data = dict(json.loads(manifest_path.read_text()))
        if data.get("extend_theme", "") is None:
            del data["extend_theme"]
        data["base_path"] = str(manifest_path.parent)
        return LegacyTheme(**data)
    except (OSError, TypeError, ValueError, KeyError) as e:
        logger.warning("Ignoring theme manifest '%s' (%s): %s", manifest_path, type(e).__name__, e)
        return None


def get_themes() -> dict[str, Theme]:
    """
    Gets a dict with the theme name as the key and theme as the value
    """
    user_themes = Path(paths.USER_THEMES)
    # legacy Ulauncher manifest themes
    manifest_themes = [t for t in map(_load_legacy_theme, user_themes.glob("**/manifest.json")) if t is not None]

    # A css file a manifest already describes is the same theme found twice. The name collision
    # below resolves to whichever came first, so drop the css duplicate rather than order these.
    manifest_css_paths = {theme.get_css_path() for theme in manifest_themes}
    css_paths = [
        *Path(paths.SYSTEM_THEMES).glob("*.css"),
        *user_themes.glob("*.css"),
    ]
    css_themes = [Theme(name=p.stem, base_path=str(p.parent)) for p in css_paths if p not in manifest_css_paths]

    themes: dict[str, Theme] = {}
    for theme in [*manifest_themes, *css_themes]:
        try:
            theme.validate()
            if themes.get(theme.name):
                logger.warning("Duplicate theme name '%s'", theme.name)
            else:
                themes[theme.name] = theme
        except (ValueError, OSError) as e:
            logger.warning(
                "Ignoring invalid or broken theme '%s' in '%s' (%s): %s",
                theme.name,
                theme.base_path,
                type(e).__name__,
                e,
            )

    return themes


class Theme(JsonConf):
    name: str = ""
    base_path: str = ""  # Runtime value, should not be stored

    def get_css_path(self) -> Path:
        return Path(self.base_path, f"{self.name}.css")

    def get_shadow_css(self, shadow_size: int) -> str:
        return "\n.app { box-shadow: 0 0 " + str(max(0, shadow_size)) + "px rgba(0, 0, 0, 0.5); }"

    def get_css(self, shadow_size: int) -> str:
        css = self.get_css_path().read_text()
        # Convert relative links to absolute
        return (
            CSS_RESET
            + re.sub(r"(?<=url\([\"\'])(\./)?(?!\/)", f"{self.base_path}/", css)
            + self.get_shadow_css(shadow_size)
        )

    def validate(self) -> None:
        if not self.get_css_path().is_file():
            msg = f"{self.get_css_path()} is not a file"
            raise ThemeError(msg)

    @classmethod
    def load(cls, theme_name: str) -> Theme:  # type: ignore[override]
        # Note: This return type should not be made a generic because it will return either Theme or LegacyTheme
        # depending on what the theme is. LegacyTheme is a Theme subclass though.
        themes = get_themes()
        if theme_name in themes:
            return themes[theme_name]

        logger.warning("Couldn't load theme: '%s'", theme_name)

        if theme_name != DEFAULT_THEME and DEFAULT_THEME in themes:
            return themes[DEFAULT_THEME]

        # Return the first on the list if everything else fails
        return next(iter(themes.values()))


class LegacyTheme(Theme):
    css_file: str = ""
    extend_theme: str = ""
    matched_text_hl_colors: dict[str, str] = {}

    def get_css_path(self) -> Path:
        # `css_file_gtk_3.20+` is the only supported one if both are specified, otherwise css_file is
        return Path(self.base_path, self.get("css_file_gtk_3.20+", self.css_file))

    def get_css(self, shadow_size: int) -> str:
        css = self.get_css_path().read_text()
        # Convert relative links to absolute
        css = CSS_RESET + re.sub(r"(?<=url\([\"\'])(\./)?(?!\/)", f"{self.base_path}/", css)
        if self.extend_theme:
            parent_theme = LegacyTheme.load(self.extend_theme)
            if parent_theme.get_css_path().is_file():
                css = f"{parent_theme.get_css(shadow_size)}\n\n{css}"
            else:
                logger.error('Cannot extend theme "%s". It does not exist', self.extend_theme)
        if highlight_color := self.matched_text_hl_colors.get("when_not_selected"):
            css += f".item-highlight {{ color: {highlight_color} }}"
        if selected_highlight_color := self.matched_text_hl_colors.get("when_selected"):
            css += f".selected.item-box .item-highlight {{ color: {selected_highlight_color} }}"
        return css + self.get_shadow_css(shadow_size)

    def validate(self) -> None:
        for prop in ["name", "css_file"]:
            if not self.get(prop):
                msg = f'"{prop}" is empty'
                raise ThemeError(msg)
        if not self.get_css_path().is_file():
            msg = f"{self.get_css_path()} is not a file"
            raise ThemeError(msg)


class ThemeError(ValueError):
    pass
