from configparser import ConfigParser
from pathlib import Path

# This file is overwritten by the build_wrapper script in setup.py
# IF YOU EDIT THIS FILE make sure your changes are reflected there

config = ConfigParser()
config.read('setup.cfg')


# __assets_dir__ is by default `<ulauncher_path>/../data/` in trunk
# and `/usr/share/ulauncher` in an installed version
__assets_dir__ = f'{Path(__file__).resolve().parent.parent}/data'
__version__ = config['metadata']['version']
