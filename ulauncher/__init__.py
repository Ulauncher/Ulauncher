# Eventually switch to define the version/gi_versions in pyproject.toml? see PR 1312

import os

from . import paths

app_id = "io.ulauncher.Ulauncher"
dbus_path = "/" + app_id.replace(".", "/")
version = "6.0.0-beta27"
api_version = "3.0"
first_run = not os.path.exists(paths.CONFIG)  # If there is no config dir, assume it's the first run
first_v6_run = not os.path.exists(paths.STATE)
gi_versions = {
    "Gtk": "3.0",
    "Gdk": "3.0",
    "GdkX11": "3.0",
    "GdkPixbuf": "2.0",
    "Pango": "1.0",
}

# this namespace module is the only way we can pin gi versions globally,
# but we also use it when we build, then we don't want to require gi
try:
    import gi

    gi.require_versions(gi_versions)
except ModuleNotFoundError:
    pass
