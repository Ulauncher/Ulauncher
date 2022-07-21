import argparse
import os
from functools import lru_cache
from gettext import gettext
from ulauncher import ASSETS, VERSION
from ulauncher.utils.migrate import v5_to_v6

API_VERSION = "3.0"
# spec: https://specifications.freedesktop.org/menu-spec/latest/ar01s02.html
APPLICATION = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
HOME = os.path.expanduser("~")
CACHE = os.path.join(os.environ.get("XDG_CACHE_HOME", f"{HOME}/.cache"), "ulauncher_cache")  # See issue#40
CONFIG = os.path.join(os.environ.get("XDG_CONFIG_HOME", f"{HOME}/.config"), "ulauncher")
DATA = os.path.join(os.environ.get("XDG_DATA_HOME", f"{HOME}/.local/share"), "ulauncher")
STATE = os.path.join(os.environ.get("XDG_STATE_HOME", f"{HOME}/.local/state"), "ulauncher")
EXTENSIONS = os.path.join(DATA, "extensions")


# Would use SimpleNamespace if that worked with typing and auto-completion.
# pylint: disable=too-few-public-methods
class _PATHS_CLASS:
    APPLICATION = APPLICATION
    ASSETS = ASSETS
    HOME = HOME
    CACHE = CACHE
    CONFIG = CONFIG
    DATA = DATA
    STATE = STATE
    EXTENSIONS = EXTENSIONS


PATHS = _PATHS_CLASS()

FIRST_RUN = not os.path.exists(PATHS.CONFIG)  # If there is no config dir, assume it's the first run
FIRST_V6_RUN = not os.path.exists(PATHS.STATE)

if not os.path.exists(PATHS.ASSETS):
    raise OSError(PATHS.ASSETS)

os.makedirs(PATHS.CACHE, exist_ok=True)
os.makedirs(PATHS.CONFIG, exist_ok=True)
os.makedirs(PATHS.STATE, exist_ok=True)
os.makedirs(PATHS.EXTENSIONS, exist_ok=True)

v5_to_v6(PATHS, FIRST_V6_RUN)


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
