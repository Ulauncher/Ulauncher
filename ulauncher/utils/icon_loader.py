import logging
from gi.repository import Gtk, Gio
from ulauncher.helpers import load_image

ICON_SIZE = 40
icon_theme = Gtk.IconTheme.get_default()
logger = logging.getLogger(__name__)


def get_app_icon_pixbuf(app, icon_size=ICON_SIZE):
    """
    :param Gio.DesktopAppInfo app:
    :param int icon_size:
    """
    icon = app.get_icon()

    if isinstance(icon, Gio.ThemedIcon):
        try:
            icon_name = icon.get_names()[0]
            return get_themed_icon_by_name(icon_name, icon_size)
        except Exception as e:
            logger.warn('Could not load icon for %s. E: %s' % (app.get_string('Icon'), e))

    elif isinstance(icon, Gio.FileIcon):
        return load_image(icon.get_file().get_path(), icon_size)

    elif isinstance(icon, str):
        return load_image(icon, icon_size)


def get_themed_icon_by_name(icon_name, icon_size=ICON_SIZE):
    # TODO: use icon_theme.choose_icon([], ..)
    # Also update all code that calls this fn. to provide alternative names
    return icon_theme.load_icon(icon_name, icon_size, Gtk.IconLookupFlags.FORCE_SIZE)
