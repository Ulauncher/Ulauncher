from configparser import ConfigParser
from pathlib import Path
import gi


class CaseSensitiveConfigParser(ConfigParser):
    def optionxform(self, optionstr):
        return optionstr


# This file is overwritten by the build_wrapper script in setup.py
# IF YOU EDIT THIS FILE make sure your changes are reflected there

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
config = CaseSensitiveConfigParser()
config.read(f"{_PROJECT_ROOT}/setup.cfg")

# Pin dependencies
gi.require_versions(dict(config["gi_versions"]))

# ASSETS is by default `<ulauncher_path>/../data/` in trunk
# and `/usr/share/ulauncher` in an installed version
ASSETS = f"{_PROJECT_ROOT}/data"
VERSION = config["metadata"]["version"]
