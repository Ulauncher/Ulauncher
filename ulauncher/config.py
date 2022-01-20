# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: Bind a new key
# Where your project will look for your data (for instance, images and ui
# files). By default, this is ../data, relative your trunk layout
# pylint: disable=deprecated-module
import argparse
import os
import string
from uuid import uuid4
from time import time
from functools import lru_cache
from gettext import gettext
from ulauncher import __version__ as VERSION, __assets_dir__ as ASSETS_DIR

_HOME = os.path.expanduser('~')
_XDG_STATE_HOME = os.environ.get('XDG_STATE_HOME') or os.path.join(_HOME, '.local', 'state')
_XDG_DATA_HOME = os.environ.get('XDG_DATA_HOME') or os.path.join(_HOME, '.local', 'share')
_XDG_CONFIG_HOME = os.environ.get('XDG_CONFIG_HOME') or os.path.join(_HOME, '.config')
_XDG_CACHE_HOME = os.environ.get('XDG_CACHE_HOME') or os.path.join(_HOME, '.cache')

API_VERSION = '2.0'
STATE_DIR = os.path.join(_XDG_STATE_HOME, 'ulauncher')
DATA_DIR = os.path.join(_XDG_DATA_HOME, 'ulauncher')
# Use ulauncher_cache dir because of the WebKit bug
# https://bugs.webkit.org/show_bug.cgi?id=151646
CACHE_DIR = os.path.join(_XDG_CACHE_HOME, 'ulauncher_cache')
CONFIG_DIR = os.path.join(_XDG_CONFIG_HOME, 'ulauncher')
SETTINGS_FILE_PATH = os.path.join(CONFIG_DIR, 'settings.json')
# spec: https://specifications.freedesktop.org/menu-spec/latest/ar01s02.html
EXTENSIONS_DIR = os.path.join(DATA_DIR, 'extensions')
EXT_PREFERENCES_DIR = os.path.join(CONFIG_DIR, 'ext_preferences')
ULAUNCHER_APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
FIRST_RUN = False
# 1..9, then a..z
ITEM_SHORTCUT_KEYS = list(map(str, range(1, 10))) + list(string.ascii_lowercase)


class AssetsPathNotFoundError(Exception):
    """Raised when we can't find the Ulauncher assets directory."""


if not os.path.exists(ASSETS_DIR):
    raise AssetsPathNotFoundError(ASSETS_DIR)

if not os.path.exists(CONFIG_DIR):
    # If there is no config dir, assume it's the first run
    FIRST_RUN = True
    os.makedirs(CONFIG_DIR)

if not os.path.exists(STATE_DIR):
    os.makedirs(STATE_DIR)

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)


def get_asset(*path_segments):
    """Get the full path to a data file.

    :returns: path to a file underneath the data directory (as defined by ASSETS_DIR`).
              Equivalent to :code:`os.path.join(ASSETS_DIR, *path_segments)`.
    """
    return os.path.join(ASSETS_DIR, *path_segments)


@lru_cache()
def get_options():
    """Support for command line options"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--verbose", action="count", dest="verbose",
        help=gettext("Show debug messages"))
    parser.add_argument(
        '--version', action='version',
        version=f"Ulauncher {VERSION}")
    parser.add_argument(
        "--no-window", action="store_true",
        help=gettext("Hide window upon application startup"))
    parser.add_argument(
        "--no-extensions", action="store_true",
        help=gettext("Do not run extensions"))
    parser.add_argument(
        "--dev", action="store_true",
        help=gettext("Enables context menu in the Preferences UI"))
    parser.add_argument(
        "--no-window-shadow", action="store_true",
        help=argparse.SUPPRESS)
    parser.add_argument(
        "--hide-window", action="store_true",
        help=argparse.SUPPRESS)

    return parser.parse_args()


def get_default_shortcuts():
    google = {
        "id": str(uuid4()),
        "name": "Google Search",
        "keyword": "g",
        "cmd": "https://google.com/search?q=%s",
        "icon": get_asset('icons/google-search.png'),
        "is_default_search": True,
        "run_without_argument": False,
        "added": time()
    }
    stackoverflow = {
        "id": str(uuid4()),
        "name": "Stack Overflow",
        "keyword": "so",
        "cmd": "https://stackoverflow.com/search?q=%s",
        "icon": get_asset('icons/stackoverflow.svg'),
        "is_default_search": True,
        "run_without_argument": False,
        "added": time()
    }
    wikipedia = {
        "id": str(uuid4()),
        "name": "Wikipedia",
        "keyword": "wiki",
        "cmd": "https://en.wikipedia.org/wiki/%s",
        "icon": get_asset('icons/wikipedia.png'),
        "is_default_search": True,
        "run_without_argument": False,
        "added": time()
    }

    return {
        google['id']: google,
        stackoverflow['id']: stackoverflow,
        wikipedia['id']: wikipedia,
    }
