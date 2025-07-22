from __future__ import annotations

import argparse
from functools import lru_cache
from gettext import gettext as _

from ulauncher import version


class CLIArguments(argparse.Namespace):
    daemon: bool
    dev: bool
    verbose: bool
    hide_window: bool
    no_extensions: bool
    no_window: bool
    no_window_shadow: bool


@lru_cache(maxsize=None)
def get_cli_args() -> CLIArguments:
    """Command Line options for the initial ulauncher (daemon) call"""
    # Python's argparse is very similar to Gtk.Application.add_main_option_entries,
    # but GTK adds in their own options we don't want like --help-gtk --help-gapplication --help-all
    parser = argparse.ArgumentParser(
        None,
        None,
        "Ulauncher is a GTK application launcher with support for extensions, shortcuts (scripts), calculator, file browser and custom themes.",  # noqa: E501
        add_help=False,
    )

    parser.add_argument("-h", "--help", action="help", help=_("Show this help message and exit"))
    parser.add_argument("-v", "--verbose", action="store_true", help=_("Show debug log messages"))
    parser.add_argument(
        "--version", action="version", help=_("Show version number and exit"), version=f"Ulauncher {version}"
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help=_("Run Ulauncher as a background process, without initially showing the window"),
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help=_("Developer mode (enables verbose logging and Preferences UI context menu)"),
    )

    # deprecated
    parser.add_argument("--hide-window", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--no-extensions", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--no-window", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--no-window-shadow", action="store_true", help=argparse.SUPPRESS)

    args = parser.parse_args(namespace=CLIArguments())
    if args.dev:
        args.verbose = True

    return args
