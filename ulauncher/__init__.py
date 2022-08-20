from configparser import ConfigParser
from pathlib import Path
import gi

# This file is overwritten by the build_wrapper script in setup.py
# IF YOU EDIT THIS FILE make sure your changes are reflected there

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
config = ConfigParser()
config.read(f"{_PROJECT_ROOT}/setup.cfg")


# ASSETS is by default `<ulauncher_path>/../data/` in trunk
# and `/usr/share/ulauncher` in an installed version
ASSETS = f"{_PROJECT_ROOT}/data"
VERSION = config["metadata"]["version"]
DESCRIPTION = config["metadata"]["description"]

gi.require_versions({
    "Gtk": "3.0",
    "Gdk": "3.0",
    "GdkX11": "3.0",
    "GdkPixbuf": "2.0",
    "Keybinder": "3.0",
    "Wnck": "3.0",
})
