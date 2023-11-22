# This file has to exist for `pytest` to find the ulauncher module

import os

os.environ["ULAUNCHER_SYSTEM_DATA_DIR"] = f"{os.path.dirname(__file__)}/data"
