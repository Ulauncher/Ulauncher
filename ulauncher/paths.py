import os
import sys

_data_dirs = os.environ.get("XDG_DATA_DIRS") or f"/usr/local/share/{os.path.pathsep}/usr/share/"

# spec: https://specifications.freedesktop.org/menu-spec/latest/ar01s02.html
APPLICATION = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BIN_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
# ULAUNCHER_SYSTEM_PREFIX can be used by third party packagers like Nix
# If not set, derive sys prefix from binary location likely /usr, /usr/local, or ~/.local
SYSTEM_PREFIX = os.environ.get("ULAUNCHER_SYSTEM_PREFIX") or os.path.dirname(BIN_DIR)
# ULAUNCHER_SYSTEM_DATA_DIR is used when running in dev mode from source and during tests
ASSETS = os.path.abspath(os.environ.get("ULAUNCHER_SYSTEM_DATA_DIR") or f"{SYSTEM_PREFIX}/share/ulauncher")
HOME = os.path.expanduser("~")
CACHE = os.path.join(os.environ.get("XDG_CACHE_HOME") or f"{HOME}/.cache", "ulauncher")
XDG_DATA_DIRS = [p for p in _data_dirs.split(os.path.pathsep) if p]
CONFIG = os.path.join(os.environ.get("XDG_CONFIG_HOME") or f"{HOME}/.config", "ulauncher")
DATA = os.path.join(os.environ.get("XDG_DATA_HOME") or f"{HOME}/.local/share", "ulauncher")
STATE = os.path.join(os.environ.get("XDG_STATE_HOME") or f"{HOME}/.local/state", "ulauncher")
USER_EXTENSIONS = os.path.join(DATA, "extensions")
# Scratch dirs, kept out of every scanned install root so a partial download can never be
# mistaken for an installed extension or theme. Under DATA so the post-install swap is a same-filesystem rename.
EXTENSIONS_STAGING = os.path.join(DATA, ".staging", "extensions")
THEMES_STAGING = os.path.join(DATA, ".staging", "themes")
PENDING_STAGING = os.path.join(DATA, ".staging", "pending")
STAGING_ROOTS = (EXTENSIONS_STAGING, THEMES_STAGING, PENDING_STAGING)
# Bare-clone cache keyed by extension id. Disposable: a missing or half-written clone is re-cloned.
REPO_CACHE = os.path.join(DATA, ".repo-cache")
ALL_EXTENSIONS_DIRS = [USER_EXTENSIONS, *[os.path.join(p, "ulauncher", "extensions") for p in XDG_DATA_DIRS]]
EXTENSIONS_CONFIG = os.path.join(CONFIG, "ext_preferences")
EXTENSIONS_STATE = os.path.join(STATE, "ext_state")
USER_THEMES = os.path.join(CONFIG, "user-themes")
SYSTEM_THEMES = os.path.join(ASSETS, "themes")
INSTALLED_THEMES = os.path.join(DATA, "themes")
THEMES_STATE = os.path.join(STATE, "theme_state")
LOG_FILE = os.path.join(STATE, "last.log")
PREVIEW_LOG_FILE = os.path.join(STATE, "preview.log")
