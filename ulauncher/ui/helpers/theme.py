from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from urllib.parse import urlparse

from ulauncher import paths
from ulauncher.data import Err, JsonConf

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


def _legacy_css_paths(theme: LegacyTheme) -> set[Path]:
    """Every css file a legacy manifest can describe (both the fallback and the gtk 3.20 variant)."""
    css_paths = set()
    if theme.css_file:
        css_paths.add(Path(theme.base_path, theme.css_file))
    gtk_css_file = theme.get("css_file_gtk_3.20+")
    if isinstance(gtk_css_file, str) and gtk_css_file:
        css_paths.add(Path(theme.base_path, gtk_css_file))
    return css_paths


def get_themes() -> dict[str, Theme]:
    """
    Gets a dict with the theme name as the key and theme as the value
    """
    # Deferred so startup and tests loading theme helpers don't pull in the extension stack.
    from ulauncher.internals import theme_installer

    user_themes = Path(paths.USER_THEMES)
    installed_roots = [Path(paths.INSTALLED_THEMES, repo_id) for repo_id in theme_installer.installed_ids()]
    # legacy Ulauncher manifest themes
    manifest_paths = [
        *user_themes.glob("**/manifest.json"),
        *(p for root in installed_roots for p in root.glob("**/manifest.json")),
    ]
    manifest_themes = [t for t in map(_load_legacy_theme, manifest_paths) if t is not None]

    # A css file a manifest already describes is the same theme found twice. The name collision
    # below resolves to whichever came first, so drop the css duplicate rather than order these.
    manifest_css_paths = set()
    for theme in manifest_themes:
        manifest_css_paths.update(_legacy_css_paths(theme))

    # An installed repo owned by a valid root manifest is a single manifest theme: its css files
    # (the declared ones and any stray like a build artifact) must not surface as standalone themes.
    # The user themes root is shared, so its css files are only dropped by exact path above.
    manifest_dirs = set()
    for theme in manifest_themes:
        try:
            theme.validate()
        except (ValueError, OSError):
            continue
        manifest_dirs.add(theme.base_path)
    system_themes = [Theme(name=p.stem, base_path=str(p.parent)) for p in Path(paths.SYSTEM_THEMES).glob("*.css")]
    css_paths = [
        *user_themes.glob("*.css"),
        *(p for root in installed_roots if str(root) not in manifest_dirs for p in root.glob("*.css")),
    ]
    css_themes = [Theme(name=p.stem, base_path=str(p.parent)) for p in css_paths if p not in manifest_css_paths]

    themes: dict[str, Theme] = {}
    for theme in [*system_themes, *manifest_themes, *css_themes]:
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


def get_theme_source(theme: Theme) -> str | None:
    """The "owner/repo" an installed theme came from, or None for user and system themes."""
    from ulauncher.internals import theme_installer
    from ulauncher.internals.install_source import parse_repo_url

    base_path = Path(theme.base_path)
    for repo_id in theme_installer.installed_ids():
        installed_root = Path(paths.INSTALLED_THEMES, repo_id)
        if base_path != installed_root and installed_root not in base_path.parents:
            continue
        parsed = parse_repo_url(theme_installer.load_state(repo_id).url)
        if isinstance(parsed, Err) or not parsed.value.browser_url:
            return None
        url_parts = urlparse(parsed.value.browser_url)
        if url_parts.scheme not in ("http", "https") or not url_parts.netloc:
            return None
        return url_parts.path.strip("/")
    return None


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
            parent_theme = get_themes().get(self.extend_theme)
            if parent_theme and parent_theme.get_css_path().is_file():
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
