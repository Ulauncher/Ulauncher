import os
import logging
from copy import copy
from ulauncher.config import CACHE_DIR


# The background is set with 40 plus the number of the color, and the foreground with 30
BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

# These are the sequences need to get colored ouput
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"


COLORS = {
    'WARNING': YELLOW,
    'INFO': WHITE,
    'DEBUG': BLUE,
    'CRITICAL': YELLOW,
    'ERROR': RED
}


class ColoredFormatter(logging.Formatter):
    def __init__(self, format, time_format=None, use_color=True):
        logging.Formatter.__init__(self, format, time_format)
        self.use_color = use_color

    def format(self, record):
        record = copy(record)
        levelname = record.levelname
        if self.use_color and levelname in COLORS:
            levelname_color = COLOR_SEQ % (30 + COLORS[levelname]) + levelname + RESET_SEQ
            record.levelname = levelname_color
        return logging.Formatter.format(self, record)


def setup_logging(opts):
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    format = "%(asctime)s | %(levelname)s | %(name)s: %(funcName)s() | %(message)s"

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG if opts.verbose else logging.WARNING)
    stream_handler.setFormatter(ColoredFormatter(format))
    root.addHandler(stream_handler)

    # set up login to a file
    log_file = os.path.join(CACHE_DIR, 'last.log')
    if os.path.exists(log_file):
        os.remove(log_file)

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(format))
    root.addHandler(file_handler)
