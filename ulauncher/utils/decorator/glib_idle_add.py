from functools import wraps
import gi
gi.require_version('GLib', '2.0')
# pylint: disable=wrong-import-position
from gi.repository import GLib


def glib_idle_add(fn):
    """
    Schedules fn to run in the main GTK loop
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        GLib.idle_add(fn, *args, **kwargs)

    wrapper.original = fn

    return wrapper
