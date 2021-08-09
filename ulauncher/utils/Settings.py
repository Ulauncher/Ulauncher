import os
import json
import gi
gi.require_version('GObject', '2.0')
# pylint: disable=wrong-import-position
from gi.repository import GObject

from ulauncher.utils.decorator.singleton import singleton
from ulauncher.config import SETTINGS_FILE_PATH

DEFAULT_BLACKLISTED_DIRS = [
    '/usr/share/locale',
    '/usr/share/app-install',
    '/usr/share/kservices5',
    '/usr/share/fk5',
    '/usr/share/kservicetypes5',
    '/usr/share/applications/screensavers',
    '/usr/share/kde4',
    '/usr/share/mimelnk'
]

GPROPERTIES = {
    "hotkey-show-app": (str,  # type
                        "Hotkey: Show ulauncher window",  # nick name
                        None,  # description
                        "<Primary>space",  # default
                        GObject.ParamFlags.READWRITE),  # flags
    "show-indicator-icon": (bool,
                            "Show app indicator",
                            None,
                            True,
                            GObject.ParamFlags.READWRITE),
    "show-recent-apps": (str,
                         "Number of recent apps",
                         None,
                         "0",
                         GObject.ParamFlags.READWRITE),
    "clear-previous-query": (bool,
                             "Clear query when app looses focus",
                             None,
                             True,
                             GObject.ParamFlags.READWRITE),
    "theme-name": (str,
                   "Current theme",
                   None,
                   "light",
                   GObject.ParamFlags.READWRITE),
    "blacklisted-desktop-dirs": (str,
                                 "Blacklisted desktop dirs",
                                 None,
                                 ':'.join(DEFAULT_BLACKLISTED_DIRS),
                                 GObject.ParamFlags.READWRITE),
    "render-on-screen": (str,
                         "Monitor to render on",
                         None,
                         "mouse-pointer-monitor",
                         GObject.ParamFlags.READWRITE),
    "terminal-command": (str,
                         "Terminal command",
                         None,
                         "",
                         GObject.PARAM_READWRITE),
    "grab-mouse-pointer": (bool,
                           "Grab mouse while open (prevents losing focus)",
                           None,
                           False,
                           GObject.ParamFlags.READWRITE),
}


class Settings(GObject.GObject):
    """
    Get/Set properties using :code:`settings.get_property('prop-name')` or
    :code:`settings.set_property('prop-name', 'new value')`

    Subscribe to property changes:

    >>> def on_notify(settings, prop):
    ...     print(prop.name)
    >>>
    >>> settings.connect("notify::hotkey-show-app", on_notify)
    """

    # __gproperties__ is used only to register properties
    # More info about __gproperties__
    # http://www.pygtk.org/articles/subclassing-gobject/sub-classing-gobject-in-python.htm#d0e127
    # http://python-gtk-3-tutorial.readthedocs.org/en/latest/objects.html
    __gproperties__ = GPROPERTIES

    _filename = None
    _properties = None

    @classmethod
    @singleton
    def get_instance(cls):
        settings = cls()
        settings.load_from_file(SETTINGS_FILE_PATH)
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
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            self.save_to_file()

    def save_to_file(self):
        if not self._filename:
            return

        with open(self._filename, 'w') as f:
            json.dump(self._properties, f, indent=4, sort_keys=True)

    def do_get_property(self, prop):
        try:
            return self._properties[prop.name]
        except KeyError:
            # return default
            return GPROPERTIES[prop.name][3]

    def do_set_property(self, prop, value):
        self._properties[prop.name] = value
