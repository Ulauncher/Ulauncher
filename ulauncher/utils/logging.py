import logging

# Great reference for terminal colors: https://chrisyeh96.github.io/2020/03/28/terminal-colors.html

log_format = "%(asctime)s | %(levelname)s | %(message)s | %(name)s.%(funcName)s():%(lineno)s"


def mkcolor(color, bold=False):
    if bold:
        color = f"1;{color}"
    return f"\x1b[{color}m"


def color_highlight(input, highlight, color, bold=False, symbol="", replace=None):
    if symbol:
        symbol = f"{symbol}  "

    return input.replace(highlight, f"{symbol}{mkcolor(color, bold)}{replace or highlight}{mkcolor(0)}")


class ColoredFormatter(logging.Formatter):
    formats = {
        logging.DEBUG: ("ℹ️", 34),  # blue
        logging.INFO: ("ℹ️", 37),  # white
        logging.WARNING: ("⚠️", 33),  # yellow
        logging.ERROR: ("⚠️", 31),  # red
        logging.CRITICAL: ("⚠️", 31),  # red
    }

    def format(self, record):
        symbol, color = self.formats.get(record.levelno, ("", 0))
        fmt_colorized_level = color_highlight(self._fmt, "| %(levelname)s |", color, True, symbol, "%(levelname)s")
        fmt_colorized = color_highlight(fmt_colorized_level, "%(name)s.%(funcName)s():%(lineno)s", 2)  # 2 means faded

        formatter = logging.Formatter(fmt_colorized)
        return formatter.format(record)
