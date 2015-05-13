import os
import json
from gi.repository import GObject
from distutils.dir_util import mkpath

GPROPERTIES = {
    "hotkey-show-app": (str,  # type
                        "Hotkey: Show ulauncher window",  # nick name
                        None,  # description
                        "<Primary>space",  # default
                        GObject.PARAM_READWRITE),  # flags
    "show-indicator-icon": (bool,
                            "Show app indicator",
                            None,
                            True,
                            GObject.PARAM_READWRITE)
}


class Settings(GObject.GObject):
    """
    Get/Set properties using
        settings.get_property('prop-name')
    or
        settings.set_property('prop-name', 'new value')

    Subscribe to property changes:

        def on_notify(settings, prop):
            print prop.name

        settings.connect("notify::hotkey-show-app", on_notify)
    """

    # __gproperties__ is used only to register properties
    # More info about __gproperties__
    # http://www.pygtk.org/articles/subclassing-gobject/sub-classing-gobject-in-python.htm#d0e127
    # http://python-gtk-3-tutorial.readthedocs.org/en/latest/objects.html
    __gproperties__ = GPROPERTIES

    _filename = None
    _properties = None

    @classmethod
    def new_from_file(cls, filename):
        settings = cls()
        settings.load_from_file(filename)
        return settings

    def __init__(self):
        GObject.GObject.__init__(self)
        self._filename = None
        self._properties = dict((name, opts[-2]) for name, opts in GPROPERTIES.items())

    def load_from_file(self, filename):
        self._filename = filename
        if os.path.exists(filename):
            if not os.path.isfile(filename):
                raise IOError("%s exists and is not a file" % filename)

            with open(filename, 'r') as f:
                self._properties = json.load(f)
        else:
            mkpath(os.path.dirname(filename))
            self.save_to_file()

    def save_to_file(self):
        if not self._filename:
            return

        with open(self._filename, 'w') as f:
            json.dump(self._properties, f, indent=4, sort_keys=True)

    def do_get_property(self, prop):
        return self._properties[prop.name]

    def do_set_property(self, prop, value):
        self._properties[prop.name] = value
