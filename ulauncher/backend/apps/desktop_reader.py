import os
from glob import glob
from itertools import chain
from gi.repository import Gio
from ulauncher_lib.helpers import recursive_search


DESKTOP_DIRS = filter(os.path.exists, map(os.path.expanduser, [
    '~/.config/ulauncher/apps',  # ulauncher specific apps
    '/usr/local/share/applications',
    '/usr/share/applications',
    '~/.local/share/applications'
]))


def find_desktop_files(dirs=DESKTOP_DIRS):
    """
    :param list dirs:
    :return list:

    TODO: search recursively
    """
    return chain.from_iterable(
        map(lambda f: os.path.join(f_path, f), recursive_search(f_path, '.desktop')) for f_path in dirs)


def filter_app(app):
    """
    :param Gio.DesktopAppInfo app:
    Returns True if app can be added to the database
    """
    return app and not (app.get_is_hidden() or app.get_nodisplay() or app.get_string('Type') != 'Application' or
                        not app.get_string('Name'))


def read_desktop_file(file):
    """
    :param str file: path to .desktop
    :return Gio.DesktopAppInfo:
    """
    try:
        return Gio.DesktopAppInfo.new_from_filename(file)
    except:
        return None


def find_apps(dirs=DESKTOP_DIRS):
    """
    :param list dirs: list of paths to *.desktop files
    :return list: list of Gio.DesktopAppInfo objects
    """
    return filter(filter_app, map(read_desktop_file, find_desktop_files(dirs)))
