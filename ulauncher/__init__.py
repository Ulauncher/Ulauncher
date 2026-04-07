import os

from . import paths
from ._version import version

__all__ = ["version"]

app_id = "io.ulauncher.Ulauncher"
dbus_path = "/" + app_id.replace(".", "/")
api_version = "3.0"
first_run = not os.path.exists(paths.CONFIG)  # If there is no config dir, assume it's the first run
first_v6_run = not os.path.exists(paths.STATE)
