import os
from typing import NoReturn

from ulauncher.cli import CLIArguments


def run(cli_args: CLIArguments) -> NoReturn:
    if cli_args.query is not None:
        escaped = cli_args.query.replace("\\", "\\\\").replace("'", "\\'")
        os.execlp("gapplication", "gapplication", "action", "io.ulauncher.Ulauncher", "set-query", f"'{escaped}'")
    else:
        os.execlp("gapplication", "gapplication", "action", "io.ulauncher.Ulauncher", "show-window")
