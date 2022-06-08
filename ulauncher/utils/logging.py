import logging
import random


def mkcolor(color, bold=False):
    if bold:
        color = f"1;{color}"
    return f"\x1b[{color}m"


class ColoredFormatter(logging.Formatter):
    formats = {
        logging.DEBUG: ("ℹ️", 34),  # blue
        logging.INFO: ("ℹ️", 37),  # white
        logging.WARNING: ("⚠️", 33),  # yellow
        logging.ERROR: ("⚠️", 31),  # red
        logging.CRITICAL: ("⚠️", 31),  # red
    }

    def format(self, record):
        # Great reference for terminal colors: https://chrisyeh96.github.io/2020/03/28/terminal-colors.html
        symbol, level_color = self.formats.get(record.levelno, ("", 0))
        prefix = f"{symbol}  {mkcolor(level_color, True)}{record.levelname}{mkcolor(0)}"
        if record.name != "root":
            # Ensure the same name gets the same color every time
            random.seed(record.name)
            name_color = random.randint(32, 37)
            prefix += f"{mkcolor(name_color, True)} {record.name}{mkcolor(0)}:"
        suffix = f"{mkcolor(2)}{record.module}.{record.funcName}:{record.lineno}{mkcolor(0)}"  # 2 means faded
        formatter = logging.Formatter(f"%(asctime)s {prefix} %(message)s {suffix}")
        return formatter.format(record)
