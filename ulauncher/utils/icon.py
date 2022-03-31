import logging
import mimetypes
from os.path import join
from functools import lru_cache

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
# pylint: disable=wrong-import-position
from gi.repository import Gtk, GdkPixbuf
from ulauncher.config import get_asset

icon_theme = Gtk.IconTheme.get_default()
logger = logging.getLogger(__name__)

DEFAULT_EXE_ICON = get_asset("icons/executable.png")


def get_icon_path(icon, size=32, base_path=""):
    """
    :param str icon:
    :rtype: str
    """
    try:
        if icon and isinstance(icon, str):
            if icon.startswith("/"):
                return icon

            if "/" in icon or mimetypes.guess_type(icon)[0]:
                return join(base_path, icon)

            themed_icon = icon_theme.lookup_icon(icon, size, Gtk.IconLookupFlags.FORCE_SIZE)
            return themed_icon.get_filename()

    except Exception as e:
        logger.info('Could not load icon path %s. E: %s', icon, e)

    return None


@lru_cache(maxsize=50)
def load_icon(icon, size):
    """
    :param str icon:
    :param int size:
    :rtype: :class:`GtkPixbuf`
    """
    try:
        icon_path = get_icon_path(icon, size) or DEFAULT_EXE_ICON
        return GdkPixbuf.Pixbuf.new_from_file_at_size(icon_path, size, size)
    except Exception as e:
        if icon_path == DEFAULT_EXE_ICON:
            raise RuntimeError(f"Could not load fallback icon: {icon_path}") from e

        logger.warning("Could not load specified icon %s (%s). Will use fallback icon", icon, e)
        return load_icon(DEFAULT_EXE_ICON, size)
