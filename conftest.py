# This file has to exist for `pytest` to find the ulauncher module

import os

# These shouldn't be written to, but 
TEST_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "./.tmp/ulauncher_tests"))

mock_xdg_dirs = {
    "XDG_CONFIG_HOME": f"{TEST_ROOT}/.xdg-home-config",
    "XDG_DATA_HOME": f"{TEST_ROOT}/.xdg-home-share",
    "XDG_STATE_HOME": f"{TEST_ROOT}/.xdg-home-state",
}

for path in mock_xdg_dirs.values():
    os.makedirs(path, exist_ok=True)

os.environ.update(mock_xdg_dirs, ULAUNCHER_SYSTEM_DATA_DIR=f"{os.path.dirname(__file__)}/data")
