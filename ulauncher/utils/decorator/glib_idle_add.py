from functools import wraps
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
