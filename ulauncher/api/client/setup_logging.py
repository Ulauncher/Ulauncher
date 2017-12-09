import os
import sys
import logging
from random import randint

RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"


def setup_logging():
    root = logging.getLogger()

    ext_name = COLOR_SEQ % (30 + randint(1, 8)) + get_extension_name() + RESET_SEQ
    formatter = logging.Formatter(
        ext_name + " | %(asctime)s | %(levelname)s | %(name)s: %(funcName)s() | %(message)s")

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root.addHandler(handler)
    root.setLevel(logging.WARNING)

    if os.getenv('VERBOSE'):
        root.setLevel(logging.DEBUG)


def get_extension_name():
    return os.path.basename(os.path.dirname(sys.argv[0]))
