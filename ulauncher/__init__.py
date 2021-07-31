from pathlib import Path
from subprocess import check_output

# This file is overwritten by the build_wrapper script in setup.py
# IF YOU EDIT THIS FILE make sure your changes are reflected there


def _exec_get_(*args):
    try:
        return check_output(list(args)).decode('utf-8').rstrip()
    except FileNotFoundError:
        return ""


__data_directory__ = f'{Path(__file__).resolve().parent.parent}/data'
__is_dev__ = True
__version__ = _exec_get_("git", "describe", "--tags") or _exec_get_("./setup.py", "--version") or "DEV"
