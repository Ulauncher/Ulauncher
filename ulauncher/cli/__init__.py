from __future__ import annotations

import argparse
import importlib
import sys
from typing import Any, Callable, Literal, cast

from ulauncher import version
from ulauncher.data import BaseDataClass
from ulauncher.init_helpers import configure_logging, ensure_runtime_dirs
from ulauncher.utils.lru_cache import lru_cache

CommandName = Literal["extensions", "install", "uninstall", "upgrade", "preview"]


class CLIArguments(argparse.Namespace):
    daemon: bool
    dev: bool  # deprecated
    verbose: bool
    hide_window: bool  # deprecated
    no_extensions: bool  # deprecated
    no_window: bool  # deprecated unreleased alias for hide_window (made more sense semantically)
    no_window_shadow: bool  # deprecated
    input: str
    path: str
    with_debugger: bool
    command: CommandName | None


CLICommandHandler = Callable[[CLIArguments], bool]


class CLICommandArgument(BaseDataClass):
    args: tuple[str, ...] = ()
    kwargs: dict[str, Any] = {}


class CLICommand(BaseDataClass):
    handler_path: str = ""
    description: str = ""
    aliases: tuple[str, ...] = ()
    arguments: tuple[CLICommandArgument, ...] = ()


@lru_cache(maxsize=None)
def get_args() -> CLIArguments:
    """Get the command line arguments for the current runtime."""
    return parse(sys.argv[1:])


@lru_cache(maxsize=None)
def _get_commands() -> dict[CommandName, CLICommand]:
    return {
        "extensions": CLICommand(
            handler_path="ulauncher.cli.commands.extensions:run",
            aliases=("e",),
            description="List installed extensions",
        ),
        "install": CLICommand(
            handler_path="ulauncher.cli.commands.install:run",
            aliases=("i",),
            description="Install an extension from a Git URL or local path",
            arguments=(
                CLICommandArgument(args=("input",), kwargs={"help": "Git URL or path of the extension to install"}),
            ),
        ),
        "uninstall": CLICommand(
            handler_path="ulauncher.cli.commands.uninstall:run",
            aliases=("rm",),
            description="Remove an installed extension by ID or URL",
            arguments=(CLICommandArgument(args=("input",), kwargs={"help": "Extension ID or URL to uninstall"}),),
        ),
        "upgrade": CLICommand(
            handler_path="ulauncher.cli.commands.upgrade:run",
            aliases=("up",),
            description="Upgrade one or all installed extensions",
            arguments=(
                CLICommandArgument(
                    args=("input",),
                    kwargs={
                        "nargs": argparse.OPTIONAL,
                        "default": "",
                        "help": "Optional extension ID or URL to upgrade (upgrades all if not specified)",
                    },
                ),
            ),
        ),
        "preview": CLICommand(
            handler_path="ulauncher.cli.commands.preview:run",
            aliases=("pr",),
            description="Preview extension for local development (with optional debugging)",
            arguments=(
                CLICommandArgument(
                    args=("--with-debugger",),
                    kwargs={
                        "action": "store_true",
                        "default": False,
                        "help": "Start the extension with remote Python debugger enabled",
                    },
                ),
                CLICommandArgument(args=("path",), kwargs={"help": "Path to the extension source directory"}),
            ),
        ),
    }


@lru_cache(maxsize=None)
def _get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        None,
        "%(prog)s [OPTIONS] [COMMAND]",
        "Ulauncher is a GTK application launcher with support for extensions, shortcuts (scripts), calculator, file browser and custom themes.",  # noqa: E501
        add_help=False,
    )
    parser.add_argument("-h", "--help", action="help", help="Show this help message and exit")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show debug log messages")
    parser.add_argument(
        "--version",
        action="version",
        help="Show version number and exit",
        version=f"Ulauncher {version}",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run Ulauncher as a background process, without initially showing the window",
    )
    # deprecated
    parser.add_argument("--dev", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--hide-window", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--no-extensions", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--no-window", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--no-window-shadow", action="store_true", help=argparse.SUPPRESS)

    # Ensure subcommand-specific attrs are always present on the namespace
    parser.set_defaults(input="", path="", with_debugger=False)

    subparsers = parser.add_subparsers(
        prog="ulauncher",
        title="commands",
        description="Available commands",
        dest="command",
        help="Command help",
    )

    for command_name, command in _get_commands().items():
        command_parser = subparsers.add_parser(
            command_name,
            aliases=list(command.aliases),
            help=command.description,
            description=command.description,
        )
        for argument in command.arguments:
            command_parser.add_argument(*argument.args, **argument.kwargs)
        command_parser.set_defaults(command=command_name)

    return parser


@lru_cache(maxsize=None)
def _load_handler(handler_path: str) -> CLICommandHandler:
    # Keep non-selected command implementations off the default startup path.
    module_name, function_name = handler_path.split(":")
    module = importlib.import_module(module_name)
    return cast("CLICommandHandler", getattr(module, function_name))


def run_command(args: CLIArguments) -> bool:
    ensure_runtime_dirs()
    if args.command is None:
        configure_logging(verbose=args.verbose, use_app_logging=True)
        return _load_handler("ulauncher.cli.commands.app:run")(args)
    command = _get_commands()[args.command]
    configure_logging(verbose=args.verbose, use_app_logging=False)
    return _load_handler(command.handler_path)(args)


def parse(input_args: list[str]) -> CLIArguments:
    """Parse CLI arguments"""
    # Python's argparse is very similar to Gtk.Application.add_main_option_entries,
    # but GTK adds in their own options we don't want like --help-gtk --help-gapplication --help-all
    parser = _get_parser()
    return parser.parse_args(args=input_args, namespace=CLIArguments())
