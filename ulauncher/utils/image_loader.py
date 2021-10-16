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
from gi.repository import Gtk, Gio, GLib, GdkPixbuf
from ulauncher.config import get_data_file


icon_theme = Gtk.IconTheme.get_default()
logger = logging.getLogger(__name__)


@lru_cache(maxsize=50)
def load_image(path, size):
    """
    :param str path:
    :param int size:

    :rtype: :class:`GtkPixbuf` or :code:`None`
    :returns: None if :func:`new_from_file_at_size` raises error
    """
    path = os.path.expanduser(path)
    # pylint: disable=broad-except
    try:
        return GdkPixbuf.Pixbuf.new_from_file_at_size(path, size, size)
    except Exception as e:
        logger.warning('Could not load image %s. E: %s', path, e)


def get_app_icon_pixbuf(icon, icon_size, icon_name):
    """
    :param Gio.Icon icon:
    :param int icon_size:
    :param str icon_name:
    :rtype: :class:`GtkPixbuf`
    """
    pixbuf_icon = None
    # pylint: disable=broad-except

    if isinstance(icon, Gio.ThemedIcon):
        try:
            icon_name = icon.get_names()[0]
            if not icon_name:
                return None
            pixbuf_icon = get_themed_icon_by_name(icon_name, icon_size)
        except Exception as e:
            logger.info('Could not load icon for %s. E: %s', icon_name, e)

    elif isinstance(icon, Gio.FileIcon):
        pixbuf_icon = load_image(icon.get_file().get_path(), icon_size)

    elif isinstance(icon, str):
        pixbuf_icon = load_image(icon, icon_size)

    if not pixbuf_icon:
        pixbuf_icon = load_image(get_data_file('icons', 'executable.png'), icon_size)

    return pixbuf_icon


def get_themed_icon_by_name(icon_name, icon_size):
    return icon_theme.load_icon(icon_name, icon_size, Gtk.IconLookupFlags.FORCE_SIZE)


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
                return get_themed_icon_by_name(special_dir, icon_size)
            return get_themed_icon_by_name('folder', icon_size)

        mime = mimetypes.guess_type(path.get_basename())[0]
        if mime:
            return get_themed_icon_by_name(mime.replace('/', '-'), icon_size)

        if path.is_exe():
            return get_themed_icon_by_name("application-x-executable", icon_size)
    except Exception as e:
        logger.warning('Icon not found %s. %s: %s', path, type(e).__name__, e)

    return get_themed_icon_by_name("unknown", icon_size)
