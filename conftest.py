# This file has to exist for `pytest` to find the ulauncher module

import os
import sys

# These paths shouldn't be written to, but if something goes wrong at least we won't overwrite user confs
TEST_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "./.tmp/ulauncher_tests"))

mock_xdg_dirs = {
    "XDG_CONFIG_HOME": f"{TEST_ROOT}/.xdg-home-config",
    "XDG_DATA_HOME": f"{TEST_ROOT}/.xdg-home-share",
    "XDG_STATE_HOME": f"{TEST_ROOT}/.xdg-home-state",
}

for path in mock_xdg_dirs.values():
    os.makedirs(path, exist_ok=True)

os.environ.update(mock_xdg_dirs, ULAUNCHER_SYSTEM_DATA_DIR=f"{os.path.dirname(__file__)}/data")

# prevent leaking pytest arguments to ulaunchers arg parser
# this way is not recommended, but it works and avoids needing tons of fixtures
# https://stackoverflow.com/q/18668947/633921
sys.argv = [sys.argv[0]]
