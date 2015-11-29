# Where your project will look for your data (for instance, images and ui
# files). By default, this is ../data, relative your trunk layout
__ulauncher_data_directory__ = '../data/'
__license__ = 'GPL-3'
__version__ = 'VERSION'

import os

from locale import gettext as _
from xdg.BaseDirectory import xdg_config_home, xdg_cache_home

# Use ulauncher_cache dir because of the WebKit bug
# https://bugs.webkit.org/show_bug.cgi?id=151646
CACHE_DIR = os.path.join(xdg_cache_home, 'ulauncher_cache')
CONFIG_DIR = os.path.join(xdg_config_home, 'ulauncher')
SETTINGS_FILE_PATH = os.path.join(CONFIG_DIR, 'settings.json')
DESKTOP_DIRS = filter(os.path.exists, map(os.path.expanduser, [
    '/usr/local/share/applications',
    '/usr/share/applications',
    '~/.local/share/applications'
]))


class ProjectPathNotFoundError(Exception):
    """Raised when we can't find the project directory."""


def get_data_file(*path_segments):
    """Get the full path to a data file.

    Returns the path to a file underneath the data directory (as defined by
    `get_data_path`). Equivalent to os.path.join(get_data_path(),
    *path_segments).
    """
    return os.path.join(get_data_path(), *path_segments)


def get_data_path():
    """Retrieve ulauncher data path

    This path is by default <ulauncher_path>/../data/ in trunk
    and /usr/share/ulauncher in an installed version but this path
    is specified at installation time.
    """

    # Get pathname absolute or relative.
    path = os.path.join(
        os.path.dirname(__file__), __ulauncher_data_directory__)

    abs_data_path = os.path.abspath(path)
    if not os.path.exists(abs_data_path):
        raise ProjectPathNotFoundError

    return abs_data_path


def get_version():
    return __version__
