from configparser import ConfigParser
from pathlib import Path

# This file is overwritten by the build_wrapper script in setup.py
# IF YOU EDIT THIS FILE make sure your changes are reflected there

config = ConfigParser()
config.read('setup.cfg')


__data_directory__ = f'{Path(__file__).resolve().parent.parent}/data'
__is_dev__ = True
__version__ = config['metadata']['version']
