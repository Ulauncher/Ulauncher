import argparse
import os
from functools import lru_cache
from gettext import gettext
from ulauncher import ASSETS, VERSION

API_VERSION = "3.0"
# spec: https://specifications.freedesktop.org/menu-spec/latest/ar01s02.html
APPLICATION = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
HOME = os.path.expanduser("~")
CONFIG = os.path.join(os.environ.get("XDG_CONFIG_HOME", f"{HOME}/.config"), "ulauncher")
DATA = os.path.join(os.environ.get("XDG_DATA_HOME", f"{HOME}/.local/share"), "ulauncher")
STATE = os.path.join(os.environ.get("XDG_STATE_HOME", f"{HOME}/.local/state"), "ulauncher")
EXTENSIONS = os.path.join(DATA, "extensions")
EXTENSIONS_CONFIG = os.path.join(CONFIG, "ext_preferences")
USER_THEMES = os.path.join(CONFIG, "user-themes")
SYSTEM_THEMES = os.path.join(ASSETS, "themes")


# Would use SimpleNamespace if that worked with typing and auto-completion.
class _PATHS_CLASS:
    APPLICATION = APPLICATION
    ASSETS = ASSETS
    HOME = HOME
    CONFIG = CONFIG
    DATA = DATA
    STATE = STATE
    EXTENSIONS = EXTENSIONS
    EXTENSIONS_CONFIG = EXTENSIONS_CONFIG
    USER_THEMES = USER_THEMES
    SYSTEM_THEMES = SYSTEM_THEMES


PATHS = _PATHS_CLASS()

FIRST_RUN = not os.path.exists(PATHS.CONFIG)  # If there is no config dir, assume it's the first run
FIRST_V6_RUN = not os.path.exists(PATHS.STATE)

if not os.path.exists(PATHS.ASSETS):
    raise OSError(PATHS.ASSETS)

os.makedirs(PATHS.CONFIG, exist_ok=True)
os.makedirs(PATHS.STATE, exist_ok=True)
os.makedirs(PATHS.EXTENSIONS, exist_ok=True)
os.makedirs(PATHS.EXTENSIONS_CONFIG, exist_ok=True)
os.makedirs(PATHS.USER_THEMES, exist_ok=True)


@lru_cache(maxsize=None)
def get_options():
    """Command Line options for the initial ulauncher (daemon) call"""
    # Python's argparse is very similar to Gtk.Application.add_main_option_entries,
    # but GTK adds in their own options we don't want like --help-gtk --help-gapplication --help-all
    parser = argparse.ArgumentParser(None, None, "Ulauncher is an application launcher.", add_help=False)

    cli_options = [
        ("Show this help message and exit", ["-h", "--help"], {"action": "help"}),
        ("Show debug messages", ["-v", "--verbose"], {}),
        ("Show version number and exit", ["--version"], {"action": "version", "version": f"Ulauncher {VERSION}"}),
        ("Hide window upon application startup", ["--no-window"], {}),
        ("Enables context menu in the Preferences UI", ["--dev"], {}),
    ]

    for descr, args, kwargs in cli_options:
        parser.add_argument(*args, help=gettext(descr), **{**{"action": "store_true"}, **kwargs})
    for arg in ["--no-extensions", "--no-window-shadow", "--hide-window"]:
        parser.add_argument(arg, action="store_true", help=argparse.SUPPRESS)

    return parser.parse_args()
