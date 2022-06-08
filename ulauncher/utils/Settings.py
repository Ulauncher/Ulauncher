import os
import json
import logging
from gi.repository import GObject

from ulauncher.utils.decorator.singleton import singleton
from ulauncher.config import SETTINGS_FILE_PATH

logger = logging.getLogger()

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
    "raise-if-started": (bool,
                         "Try to switch to the app first, rather than launching it",
                         None,
                         False,
                         GObject.ParamFlags.READWRITE),
    "render-on-screen": (str,
                         "Monitor to render on",
                         None,
                         "mouse-pointer-monitor",
                         GObject.ParamFlags.READWRITE),

    "jump-keys": (str,
                  "The keys use for quickly jumping to results",
                  None,
                  "1234567890abcdefghijklmnopqrstuvwxyz",
                  GObject.ParamFlags.READWRITE),
    "terminal-command": (str,
                         "Terminal command",
                         None,
                         "",
                         GObject.ParamFlags.READWRITE),
    "grab-mouse-pointer": (bool,
                           "Grab mouse while open (prevents losing focus)",
                           None,
                           False,
                           GObject.ParamFlags.READWRITE),
    "disable-desktop-filters": (bool,  # type
                                "Display all apps in environment despite OnlyShowIn/NotShowIn",  # nick name
                                None,  # description
                                False,  # default
                                GObject.ParamFlags.READWRITE),  # flags
    "disable-window-shadow": (bool,
                              "Disable the shadow drawn around the Ulauncher window",
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
    # https://www.pygtk.org/articles/subclassing-gobject/sub-classing-gobject-in-python.htm#d0e127
    # https://python-gtk-3-tutorial.readthedocs.org/en/latest/objects.html
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
                raise IOError(f"{filename} exists and is not a file")

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
        return self._properties.get(prop.name, GPROPERTIES[prop.name][3])

    def do_set_property(self, prop, value):
        logger.info('Set %s to %s', prop.name, value)
        self._properties[prop.name] = value
        self.save_to_file()

    def get_all(self):
        return dict(list(map(lambda prop: (prop, getattr(self.props, prop)), dir(self.props))))

    def get_jump_keys(self):
        # convert to list and filter out duplicates
        keys_setting = list(self.get_property('jump-keys'))
        return list(dict.fromkeys(keys_setting))
