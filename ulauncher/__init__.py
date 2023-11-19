from configparser import ConfigParser
from os.path import dirname


class CaseSensitiveConfigParser(ConfigParser):
    def optionxform(self, optionstr):
        return optionstr


_project_root = dirname(dirname(__file__))
_config = CaseSensitiveConfigParser()
_config.read(f"{_project_root}/setup.cfg")

data_dir = f"{_project_root}/data"  # substituted for `{sys.prefix}/share/ulauncher` at build time
version = _config["metadata"]["version"]
description = _config["metadata"]["description"]
gi_versions = {
    "Gtk": "3.0",
    "Gdk": "3.0",
    "GdkX11": "3.0",
    "GdkPixbuf": "2.0",
    "Pango": "1.0",
}

"""
This file is written for when running Ulauncher from the source directory
When packaging Ulauncher we overwrite everything above this comment with static variables
So IF YOU EDIT THIS FILE make sure your changes are reflected in setup.py:build_wrapper
"""

# this namespace module is the only way we can pin gi versions globally,
# but we also use it when we build, then we don't want to require gi
try:
    import gi

    gi.require_versions(gi_versions)
except ModuleNotFoundError:
    pass
