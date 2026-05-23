from __future__ import annotations

import argparse
import importlib
import sys
from typing import Any, Callable, Literal, cast

from ulauncher import version
from ulauncher.data import BaseDataClass
from ulauncher.init_helpers import configure_logging, ensure_runtime_dirs
from ulauncher.utils.lru_cache import lru_cache

CommandName = Literal["show", "toggle", "start", "extensions", "install", "uninstall", "upgrade", "preview"]


class CLIArguments(BaseDataClass):
    verbose = False
    input = ""
    path = ""
    query: str | None = None
    with_debugger = False
    command: CommandName = "show"


CLICommandHandler = Callable[[CLIArguments], int]


class CLICommandArgument(BaseDataClass):
    args: tuple[str, ...] = ()
    kwargs: dict[str, Any] = {}


class CLICommand(BaseDataClass):
    summary: str = ""  # one-line, shown in the master `ulauncher --help` listing
    description: str = ""  # longer sentence, shown at the top of `ulauncher <cmd> --help`
    aliases: tuple[str, ...] = ()
    arguments: tuple[CLICommandArgument, ...] = ()
    has_runtime: bool = True


@lru_cache(maxsize=None)
def get_args() -> CLIArguments:
    """Get the command line arguments for the current runtime."""
    return parse(sys.argv[1:])


@lru_cache(maxsize=None)
def _get_commands() -> dict[CommandName, CLICommand]:
    return {
        "start": CLICommand(
            summary="Start the Ulauncher background process",
            description="Start the Ulauncher background process",
        ),
        "show": CLICommand(
            summary="Show the Ulauncher window (default command)",
            description="Show the Ulauncher window",
            has_runtime=False,
            arguments=(
                CLICommandArgument(
                    args=("query",),
                    kwargs={"nargs": argparse.OPTIONAL, "default": None, "help": "Optional query to populate"},
                ),
            ),
        ),
        "toggle": CLICommand(
            summary="Toggle the Ulauncher window",
            description="Toggle the Ulauncher window",
            has_runtime=False,
        ),
        "extensions": CLICommand(
            aliases=("e",),
            summary="List installed extensions",
            description="List all installed extensions with their status and information",
        ),
        "install": CLICommand(
            aliases=("i",),
            summary="Install an extension from URL",
            description="Install an extension from a Git URL or local path",
            arguments=(
                CLICommandArgument(args=("input",), kwargs={"help": "Git URL or path of the extension to install"}),
            ),
        ),
        "uninstall": CLICommand(
            aliases=("rm",),
            summary="Uninstall an extension",
            description="Remove an installed extension by ID or URL",
            arguments=(CLICommandArgument(args=("input",), kwargs={"help": "Extension ID or URL to uninstall"}),),
        ),
        "upgrade": CLICommand(
            aliases=("up",),
            summary="Upgrade extensions",
            description="Upgrade one or all installed extensions to their latest versions",
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
            aliases=("pr",),
            summary="Preview extension",
            description="Starts extension from a local path for development and debugging purposes",
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
        prog="ulauncher",  # override Python 3.14 argparse's `python3 -m ulauncher` auto-prog
        usage="%(prog)s [OPTIONS] [COMMAND]",
        description="Ulauncher is a GTK application launcher with support for extensions, shortcuts (scripts), calculator, file browser and custom themes.",  # noqa: E501
        add_help=False,
    )
    parser.add_argument("--version", action="version", help="Show version", version=f"Ulauncher {version}")
    parser.add_argument("-h", "--help", action="help", help="Show help")
    parser.add_argument("-v", "--verbose", action="store_true", help="Use verbose logging")

    subparsers = parser.add_subparsers(
        title="commands",
        description="Available commands",
        dest="command",
        help="Command help",
    )

    for command_name, command in _get_commands().items():
        command_parser = subparsers.add_parser(
            command_name,
            aliases=list(command.aliases),
            help=command.summary,
            description=command.description,
        )
        for argument in command.arguments:
            command_parser.add_argument(*argument.args, **argument.kwargs)
        command_parser.set_defaults(command=command_name)

    return parser


def _load_handler(command_name: str) -> CLICommandHandler:
    # Keep non-selected command implementations off the default startup path.
    module = importlib.import_module(f"ulauncher.cli.commands.{command_name}")
    return cast("CLICommandHandler", module.run)


def run_command(args: CLIArguments) -> int:
    command = _get_commands()[args.command]
    if command.has_runtime:
        ensure_runtime_dirs()
        configure_logging(verbose=args.verbose, use_app_logging=args.command == "start")
    return _load_handler(args.command)(args)


def parse(input_args: list[str]) -> CLIArguments:
    """Parse CLI arguments"""
    args = _get_parser().parse_args(args=input_args)
    namespace = vars(args)
    namespace["command"] = cast("CommandName", namespace["command"] or "show")
    return CLIArguments(**namespace)
