from gi.repository import Gtk
from distutils.version import StrictVersion


def gtk_version_is_gte(major, minor, micro):
    gtk_version = '%s.%s.%s' % (Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version())
    return StrictVersion(gtk_version) >= StrictVersion('%s.%s.%s' % (major, minor, micro))
