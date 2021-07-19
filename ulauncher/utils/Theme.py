import os
import logging
from json import load
from typing import Dict, Any
from shutil import copytree, rmtree

from ulauncher.config import get_data_path, CONFIG_DIR, CACHE_DIR
from ulauncher.utils.Settings import Settings
from ulauncher.utils.version_cmp import gtk_version_is_gte

themes = {}  # type: Dict[str, Any]
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
            themes[theme.get_name()] = theme


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

    theme_dict = None

    def __init__(self, path):
        self.path = path

    def get_manifest_version(self):
        return self._read()['manifest_version']

    def get_name(self):
        return self._read()['name']

    def get_display_name(self):
        return self._read()['display_name']

    def get_matched_text_hl_colors(self):
        return self._read()['matched_text_hl_colors']

    def get_extend_theme(self):
        return self._read()['extend_theme']

    def get_css_file(self):
        return self._read()['css_file']

    def get_css_file_gtk_3_20(self):
        return self._read()['css_file_gtk_3.20+']

    def clear_cache(self):
        self.theme_dict = None

    def _read(self):
        if self.theme_dict:
            return self.theme_dict

        with open(os.path.join(self.path, 'manifest.json'), 'r') as f:
            self.theme_dict = load(f)

        return self.theme_dict

    def validate(self):
        try:
            assert self.get_manifest_version() in ['1'], "Supported manifest version is '1'"
            assert self.get_name(), '"get_name" is empty'
            assert self.get_display_name(), '"get_display_name" is empty'
            assert self.get_matched_text_hl_colors(), '"get_matched_text_hl_colors" is empty'
            assert self.get_css_file(), '"get_css_file" is empty'
            assert self.get_css_file_gtk_3_20(), '"css_file_gtk_3.20+" is empty'
            assert os.path.exists(os.path.join(self.path, self.get_css_file())), '"css_file" does not exist'
            assert os.path.exists(os.path.join(self.path, self.get_css_file_gtk_3_20())), \
                '"css_file_gtk_3.20+" does not exist'
        except AssertionError as e:
            raise ThemeManifestError(e) from e

    def compile_css(self) -> None:
        # workaround for issue with a caret-color
        # GTK+ < 3.20 doesn't support that prop
        css_file_name = self.get_css_file_gtk_3_20() if gtk_version_is_gte(3, 20, 0) else self.get_css_file()
        css_file = os.path.join(self.path, css_file_name)

        if not self.get_extend_theme():
            return css_file

        # if theme extends another one, we must import it in css
        # therefore a new css file (generated.css) is created here
        extend_theme_name = self.get_extend_theme()
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
        new_theme_dir = os.path.join(CACHE_DIR, 'themes', self.get_name())
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
