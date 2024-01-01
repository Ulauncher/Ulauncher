from __future__ import annotations

import argparse
import os
import sys
from functools import lru_cache
from gettext import gettext

import ulauncher

APP_ID = "io.ulauncher.Ulauncher"
API_VERSION = "3.0"
# spec: https://specifications.freedesktop.org/menu-spec/latest/ar01s02.html
APPLICATION = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# ULAUNCHER_SYSTEM_PREFIX is used by a third party packagers like Nix
SYSTEM_PREFIX = os.environ.get("ULAUNCHER_SYSTEM_PREFIX", sys.prefix)
# ULAUNCHER_SYSTEM_DATA_DIR is used when running in dev mode from source and during tests
SYSTEM_DATA_DIR = os.path.abspath(os.environ.get("ULAUNCHER_SYSTEM_DATA_DIR", f"{SYSTEM_PREFIX}/share/ulauncher"))
HOME = os.path.expanduser("~")
XDG_DATA_DIRS = os.environ.get("XDG_DATA_DIRS", f"/usr/local/share/{os.path.pathsep}/usr/share/").split(os.path.pathsep)
USER_CONFIG_DIR = os.path.join(os.environ.get("XDG_CONFIG_HOME", f"{HOME}/.config"), "ulauncher")
USER_DATA_DIR = os.path.join(os.environ.get("XDG_DATA_HOME", f"{HOME}/.local/share"), "ulauncher")
USER_STATE_DIR = os.path.join(os.environ.get("XDG_STATE_HOME", f"{HOME}/.local/state"), "ulauncher")
USER_EXTENSIONS_DIR = os.path.join(USER_DATA_DIR, "extensions")
ALL_EXTENSIONS_DIRS = [USER_EXTENSIONS_DIR, *[os.path.join(p, "ulauncher", "extensions") for p in XDG_DATA_DIRS]]
EXTENSIONS_CONFIG_DIR = os.path.join(USER_CONFIG_DIR, "ext_preferences")
EXTENSIONS_STATE_DIR = os.path.join(USER_STATE_DIR, "ext_state")
USER_THEMES = os.path.join(USER_CONFIG_DIR, "user-themes")
SYSTEM_THEMES = os.path.join(SYSTEM_DATA_DIR, "themes")
VERSION = ulauncher.version


# Would use SimpleNamespace if that worked with typing and auto-completion.
class _PATHS_CLASS:
    APPLICATION = APPLICATION
    ASSETS = SYSTEM_DATA_DIR
    HOME = HOME
    CONFIG = USER_CONFIG_DIR
    DATA = USER_DATA_DIR
    STATE = USER_STATE_DIR
    USER_EXTENSIONS_DIR = USER_EXTENSIONS_DIR
    ALL_EXTENSIONS_DIRS = ALL_EXTENSIONS_DIRS
    EXTENSIONS_CONFIG = EXTENSIONS_CONFIG_DIR
    EXTENSIONS_STATE = EXTENSIONS_STATE_DIR
    USER_THEMES = USER_THEMES
    SYSTEM_THEMES = SYSTEM_THEMES


PATHS = _PATHS_CLASS()

FIRST_RUN = not os.path.exists(PATHS.CONFIG)  # If there is no config dir, assume it's the first run
FIRST_V6_RUN = not os.path.exists(PATHS.STATE)

if not os.path.exists(PATHS.ASSETS):
    raise OSError(PATHS.ASSETS)

os.makedirs(PATHS.CONFIG, exist_ok=True)
os.makedirs(PATHS.STATE, exist_ok=True)
os.makedirs(PATHS.USER_EXTENSIONS_DIR, exist_ok=True)
os.makedirs(PATHS.EXTENSIONS_CONFIG, exist_ok=True)
os.makedirs(PATHS.USER_THEMES, exist_ok=True)


@lru_cache(maxsize=None)
def get_options():
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
