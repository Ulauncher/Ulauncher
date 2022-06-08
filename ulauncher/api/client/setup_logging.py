import os
import sys
import logging
import random

from ulauncher.utils.logging import color_highlight, ColoredFormatter, log_format


def setup_logging():
    root = logging.getLogger()

    ext_name = get_extension_name()
    random.seed(ext_name)
    colorized_ext_name = color_highlight(ext_name, ext_name, random.randint(32, 37), True)
    handler = logging.StreamHandler()
    handler.setFormatter(ColoredFormatter(log_format.replace("%(message)s", f"{colorized_ext_name} %(message)s")))

    root.addHandler(handler)
    root.setLevel(logging.WARNING)

    if os.getenv('VERBOSE'):
        root.setLevel(logging.DEBUG)


def get_extension_name():
    return os.path.basename(os.path.dirname(sys.argv[0]))
