import os
import logging
from itertools import chain
from gi.repository import Gio

from ulauncher.util.file_finder import find_files
from ulauncher.config import DESKTOP_DIRS

logger = logging.getLogger(__name__)


def find_desktop_files(dirs=DESKTOP_DIRS):
    """
    :param list dirs:
    :rtype: list
    """
    return chain.from_iterable(
        map(lambda f: os.path.join(f_path, f), find_files(f_path, '*.desktop')) for f_path in dirs)


def filter_app(app):
    """
    :param Gio.DesktopAppInfo app:
    :returns: True if app can be added to the database
    """
    return app and not (app.get_is_hidden() or app.get_nodisplay() or app.get_string('Type') != 'Application' or
                        not app.get_string('Name'))


def read_desktop_file(file):
    """
    :param str file: path to .desktop
    :rtype: :class:`Gio.DesktopAppInfo` or :code:`None`
    """
    try:
        return Gio.DesktopAppInfo.new_from_filename(file)
    except Exception as e:
        logger.info('Could not read "%s": %s' % (file, e))
        return None


def find_apps(dirs=DESKTOP_DIRS):
    """
    :param list dirs: list of paths to `*.desktop` files
    :returns: list of :class:`Gio.DesktopAppInfo` objects
    """
    return filter(filter_app, map(read_desktop_file, find_desktop_files(dirs)))
