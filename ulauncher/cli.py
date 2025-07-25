from __future__ import annotations

import argparse
from functools import lru_cache, partial
from gettext import gettext as _

from ulauncher import version
from ulauncher.modes.extensions.extension_cli_handlers import (
    install_extension,
    list_active_extensions,
    uninstall_extension,
    upgrade_extensions,
)


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
        "%(prog)s OPTIONS or ARGUMENT",
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

    subparsers = parser.add_subparsers(
        prog="ulauncher",
        title="arguments",
        metavar="",  # keep this empty to avoid duplication of argument names
    )
    extension_help = _("Manage extensions: list, install, uninstall, upgrade")
    configure_extension_args(
        subparsers.add_parser("extensions", aliases=["e"], description=extension_help, help=extension_help)
    )

    args = parser.parse_args(namespace=CLIArguments())
    if args.dev:
        args.verbose = True

    return args


def configure_extension_args(parser: argparse.ArgumentParser) -> None:
    # list extensions on `ulauncher extensions`
    parser.set_defaults(handler=partial(list_active_extensions, parser))

    subparsers = parser.add_subparsers(
        metavar="",  # keep this empty to avoid duplication of argument names
    )

    list_parser = subparsers.add_parser("list", aliases=["ls"], help="List active extensions")
    list_parser.set_defaults(handler=partial(list_active_extensions, list_parser))

    install_parser = subparsers.add_parser("install", aliases=["i"], help="Install an extension from URL")
    install_parser.add_argument("URL", help="Git URL of the extension to install")
    install_parser.set_defaults(handler=partial(install_extension, install_parser))

    uninstall_parser = subparsers.add_parser("uninstall", aliases=["un"], help="Uninstall an extension")
    uninstall_parser.add_argument("ID_OR_URL", help="Extension ID or URL to uninstall")
    uninstall_parser.set_defaults(handler=partial(uninstall_extension, uninstall_parser))

    upgrade_parser = subparsers.add_parser("upgrade", aliases=["up"], help="Upgrade extensions")
    upgrade_parser.add_argument(
        "ID_OR_URL",
        nargs=argparse.OPTIONAL,
        help="Optional extension ID or URL to upgrade (upgrades all if not specified)",
    )
    upgrade_parser.set_defaults(handler=partial(upgrade_extensions, upgrade_parser))
