import os
import logging
import mimetypes
from functools import lru_cache

import gi
gi.require_version('GLib', '2.0')
gi.require_version('Gtk', '3.0')
gi.require_version('Gio', '2.0')
gi.require_version('GdkPixbuf', '2.0')

# pylint: disable=wrong-import-position
from gi.repository import Gtk, GLib, GdkPixbuf
from ulauncher.config import get_data_file


icon_theme = Gtk.IconTheme.get_default()
logger = logging.getLogger(__name__)

SPECIAL_DIRS = {
    GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD): 'folder-download',
    GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS): 'folder-documents',
    GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_MUSIC): 'folder-music',
    GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_PICTURES): 'folder-pictures',
    GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_PUBLIC_SHARE): 'folder-publicshare',
    GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_TEMPLATES): 'folder-templates',
    GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_VIDEOS): 'folder-videos',
    GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DESKTOP): 'user-desktop',
    os.path.expanduser('~'): 'folder-home'
}


@lru_cache(maxsize=50)
def load_icon(icon, size):
    """
    :param str icon:
    :param int size:
    :rtype: :class:`GtkPixbuf`
    """
    try:
        if icon.startswith("/"):
            return GdkPixbuf.Pixbuf.new_from_file_at_size(icon, size, size)
        return icon_theme.load_icon(icon, size, Gtk.IconLookupFlags.FORCE_SIZE)
    except Exception as e:
        logger.info('Could not load icon %s. E: %s', icon, e)
        return load_icon(get_data_file('icons', 'executable.png'), size)


def _get_themed_icon_by_name(icon_name, icon_size):
    return icon_theme.load_icon(icon_name, icon_size, Gtk.IconLookupFlags.FORCE_SIZE)


def get_file_icon(path, icon_size):
    """
    :param ~ulauncher.utils.Path.Path path:
    :param int icon_size:
    """
    # pylint: disable=broad-except
    try:
        if path.is_dir():
            special_dir = SPECIAL_DIRS.get(str(path))
            if special_dir:
                return _get_themed_icon_by_name(special_dir, icon_size)
            return _get_themed_icon_by_name('folder', icon_size)

        mime = mimetypes.guess_type(path.get_basename())[0]
        if mime:
            return _get_themed_icon_by_name(mime.replace('/', '-'), icon_size)

        if path.is_exe():
            return _get_themed_icon_by_name("application-x-executable", icon_size)
    except Exception as e:
        logger.warning('Icon not found %s. %s: %s', path, type(e).__name__, e)

    return _get_themed_icon_by_name("unknown", icon_size)
