import os
import logging
import json
from typing import Dict, Any
from shutil import copytree, rmtree

from ulauncher.config import get_data_path, CONFIG_DIR, CACHE_DIR
from ulauncher.utils.Settings import Settings
from ulauncher.utils.version_cmp import gtk_version_is_gte

themes: Dict[str, Any] = {}
logger = logging.getLogger(__name__)
user_theme_dir = os.path.join(CONFIG_DIR, 'user-themes')


def load_available_themes():
    themes.clear()
    ulauncher_theme_dir = os.path.join(get_data_path(), 'themes')
    theme_dirs = [os.path.join(ulauncher_theme_dir, d) for d in os.listdir(ulauncher_theme_dir)]
    if os.path.exists(user_theme_dir):
        theme_dirs.extend([os.path.join(user_theme_dir, d) for d in os.listdir(user_theme_dir)])
    theme_dirs = list(filter(os.path.isdir, theme_dirs))

    for dir in theme_dirs:
        if os.path.isfile(os.path.join(dir, 'manifest.json')):
            theme = Theme(dir)
            try:
                theme.validate()
            except ThemeManifestError as e:
                logger.error('%s: %s', type(e).__name__, e)
                continue
            themes[theme.get('name')] = theme


class Theme:

    @classmethod
    def get_current(cls):
        default = 'light'
        current_name = Settings.get_instance().get_property('theme-name') or default
        try:
            current = themes[current_name]
        except KeyError:
            logger.warning('No theme with name %s', current_name)
            current = themes[default]

        return current

    _data = None

    def __init__(self, path):
        self.path = path

    def clear_cache(self):
        self._data = None

    def _read(self):
        if not self._data:
            with open(os.path.join(self.path, 'manifest.json'), 'r') as file:
                self._data = json.load(file)

        return self._data

    def get(self, property: str):
        return self._read().get(property)

    def validate(self):
        try:
            assert self.get('manifest_version') in ['1'], "Supported manifest version is '1'"
            for prop in ['name', 'display_name', 'matched_text_hl_colors', 'css_file', 'css_file_gtk_3.20+']:
                assert self.get(prop), '"%s" is empty' % prop

            assert os.path.exists(os.path.join(self.path, self.get('css_file'))), '"css_file" does not exist'
            assert os.path.exists(os.path.join(self.path, self.get('css_file_gtk_3.20+'))), \
                '"css_file_gtk_3.20+" does not exist'
        except AssertionError as e:
            raise ThemeManifestError(e) from e

    def compile_css(self) -> None:
        # workaround for issue with a caret-color
        # GTK+ < 3.20 doesn't support that prop
        css_file_name = self.get('css_file_gtk_3.20+') if gtk_version_is_gte(3, 20, 0) else self.get('css_file')
        css_file = os.path.join(self.path, css_file_name)

        if not self.get('extend_theme'):
            return css_file

        # if theme extends another one, we must import it in css
        # therefore a new css file (generated.css) is created here
        extend_theme_name = self.get('extend_theme')
        try:
            extend_theme = themes[extend_theme_name]
        except KeyError:
            logger.error('Cannot extend theme "%s". It does not exist', extend_theme_name)
            return css_file

        generated_css = self._get_path_for_generated_css()
        with open(generated_css, 'w') as new_css_file:
            new_css_file.write('@import url("%s");\n\n' % extend_theme.compile_css())
            with open(css_file, 'r') as theme_css_file:
                new_css_file.write(theme_css_file.read())

        return generated_css

    def _get_path_for_generated_css(self):
        if user_theme_dir in self.path:
            return os.path.join(self.path, 'generated.css')

        # for ulauncher themes we must save generated.css elsewhere
        # because we don't have write permissions for /usr/share/ulauncher/themes/...
        new_theme_dir = os.path.join(CACHE_DIR, 'themes', self.get('name'))
        if not os.path.exists(new_theme_dir):
            os.makedirs(new_theme_dir)

        # copy current theme files to this new dir
        rmtree(new_theme_dir)
        copytree(self.path, new_theme_dir)

        # ensure correct file permissions
        os.chmod(new_theme_dir, 0o755)

        return os.path.join(new_theme_dir, 'generated.css')


class ThemeManifestError(Exception):
    pass
