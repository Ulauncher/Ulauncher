import logging
from functools import lru_cache

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
# pylint: disable=wrong-import-position
from gi.repository import Gtk, GdkPixbuf
from ulauncher.config import get_asset

icon_theme = Gtk.IconTheme.get_default()
logger = logging.getLogger(__name__)


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
        return load_icon(get_asset('icons/executable.png'), size)
