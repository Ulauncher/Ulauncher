import gi
gi.require_version('Gtk', '3.0')
# pylint: disable=wrong-import-position
from gi.repository import Gtk


def gtk_version_is_gte(major: int, minor: int, micro: int) -> bool:
    gtk_version = (Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version())
    return gtk_version >= (major, minor, micro)
