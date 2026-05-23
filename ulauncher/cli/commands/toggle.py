import os
from typing import NoReturn

from ulauncher.cli import CLIArguments


def run(_: CLIArguments) -> NoReturn:
    os.execlp("gapplication", "gapplication", "action", "io.ulauncher.Ulauncher", "toggle-window")
