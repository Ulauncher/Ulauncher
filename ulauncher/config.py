from __future__ import annotations

import argparse
import os
from functools import lru_cache
from gettext import gettext

import ulauncher
from ulauncher import paths as PATHS

APP_ID = "io.ulauncher.Ulauncher"
API_VERSION = "3.0"
VERSION = ulauncher.version
FIRST_RUN = not os.path.exists(PATHS.CONFIG)  # If there is no config dir, assume it's the first run
FIRST_V6_RUN = not os.path.exists(PATHS.STATE)

if not os.path.exists(PATHS.ASSETS):
    raise OSError(PATHS.ASSETS)

os.makedirs(PATHS.CONFIG, exist_ok=True)
os.makedirs(PATHS.STATE, exist_ok=True)
os.makedirs(PATHS.USER_EXTENSIONS, exist_ok=True)
os.makedirs(PATHS.EXTENSIONS_CONFIG, exist_ok=True)
os.makedirs(PATHS.USER_THEMES, exist_ok=True)


@lru_cache(maxsize=None)
def get_options() -> argparse.Namespace:
    """Command Line options for the initial ulauncher (daemon) call"""
    # Python's argparse is very similar to Gtk.Application.add_main_option_entries,
    # but GTK adds in their own options we don't want like --help-gtk --help-gapplication --help-all
    parser = argparse.ArgumentParser(None, None, "Ulauncher is an application launcher.", add_help=False)

    parser.add_argument("-h", "--help", action="help", help=gettext("Show this help message and exit"))
    parser.add_argument("-v", "--verbose", action="store_true", help=gettext("Show debug messages"))
    parser.add_argument(
        "--version", action="version", help=gettext("Show version number and exit"), version=f"Ulauncher {VERSION}"
    )
    parser.add_argument("--no-window", action="store_true", help=gettext("Hide window upon application startup"))
    parser.add_argument("--dev", action="store_true", help=gettext("Enables context menu in the Preferences UI"))
    parser.add_argument("--no-extensions", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--no-window-shadow", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--hide-window", action="store_true", help=argparse.SUPPRESS)

    return parser.parse_args()
