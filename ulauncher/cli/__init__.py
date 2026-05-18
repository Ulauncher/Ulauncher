from __future__ import annotations

import argparse
import importlib
import sys
from typing import Any, Callable, Literal, cast
from typing import get_args as get_literal_args

from ulauncher import version
from ulauncher.data import BaseDataClass
from ulauncher.init_helpers import configure_logging, ensure_runtime_dirs
from ulauncher.utils.lru_cache import lru_cache

CommandName = Literal["show", "toggle", "start", "extensions", "install", "uninstall", "upgrade", "preview"]
CommandGroupName = Literal["App", "Extension"]


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
    group: CommandGroupName
    aliases: tuple[str, ...] = ()
    arguments: tuple[CLICommandArgument, ...] = ()
    has_runtime: bool = True


CLI_DESCRIPTION = (
    "Ulauncher is a GTK application launcher with support for extensions, "
    "shortcuts (scripts), calculator, file browser and custom themes."
)


class CLIHelpFormatter(argparse.HelpFormatter):
    """Normalize argparse section titles used in the custom help output."""

    def start_section(self, heading: str | None) -> None:
        if heading in ("options", "optional arguments"):  # differs based on Python version
            heading = "Options"
        super().start_section(heading)


class CLIArgumentParser(argparse.ArgumentParser):
    """Render top-level help from explicit CLI metadata instead of parser internals."""

    def __init__(self, *args: Any, version: str = "", **kwargs: Any) -> None:
        super().__init__(*args, add_help=False, **kwargs)
        # Will appear at the tail of the "App commands" section in --help. Do not add to this
        # unless you know what you're doing -- Ulauncher's CLI is designed around "verbs" (e.g.
        # `ulauncher show`) implemented as sub-parsers, with flags only at the sub-parser level.
        self.help_option_actions: tuple[argparse.Action, ...] = (
            self.add_argument("--version", action="version", help="Show version", version=version),
            self.add_argument("-h", "--help", action="help", help="Show help"),
        )

    def format_help(self) -> str:
        formatter = self.formatter_class(prog=self.prog)
        formatter.add_usage(self.usage, (), (), prefix="Usage: ")
        formatter.add_text(self.description)
        _add_command_help_sections(formatter, self.help_option_actions)
        formatter.add_text(self.epilog)

        return formatter.format_help()


def _get_command_help_action(command_name: CommandName, command: CLICommand) -> argparse.Action:
    # Mirrors stdlib's argparse._SubParsersAction._ChoicesPseudoAction: an Action used purely
    # as a data carrier for the help formatter, never dispatched at parse time.
    label = command_name
    if command.aliases:
        label = f"{command_name} ({', '.join(command.aliases)})"

    return argparse.Action([], command_name, help=command.summary, metavar=label)


def _add_command_help_sections(
    formatter: argparse.HelpFormatter,
    help_option_actions: tuple[argparse.Action, ...] = (),
) -> None:
    commands = _get_commands()

    for group_name in get_literal_args(CommandGroupName):
        group_actions: list[argparse.Action] = [
            _get_command_help_action(command_name, command)
            for command_name, command in commands.items()
            if command.group == group_name
        ]
        # --help/--version live with the App commands rather than in their own "Options" section:
        # they're command-shaped (run once, print, exit) and there are no real options at the top level.
        if group_name == "App":
            group_actions.extend(help_option_actions)
        if not group_actions:
            continue

        formatter.start_section(f"{group_name} commands")
        formatter.add_arguments(group_actions)
        formatter.end_section()


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
            group="App",
        ),
        "show": CLICommand(
            summary="Show the Ulauncher window (default command)",
            description="Show the Ulauncher window",
            group="App",
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
            group="App",
            has_runtime=False,
        ),
        "extensions": CLICommand(
            aliases=("e",),
            summary="List installed extensions",
            description="List all installed extensions with their status and information",
            group="Extension",
        ),
        "install": CLICommand(
            aliases=("i",),
            summary="Install an extension from URL",
            description="Install an extension from a Git URL or local path",
            group="Extension",
            arguments=(
                CLICommandArgument(args=("input",), kwargs={"help": "Git URL or path of the extension to install"}),
            ),
        ),
        "uninstall": CLICommand(
            aliases=("rm",),
            summary="Uninstall an extension",
            description="Remove an installed extension by ID or URL",
            group="Extension",
            arguments=(CLICommandArgument(args=("input",), kwargs={"help": "Extension ID or URL to uninstall"}),),
        ),
        "upgrade": CLICommand(
            aliases=("up",),
            summary="Upgrade extensions",
            description="Upgrade one or all installed extensions to their latest versions",
            group="Extension",
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
            group="Extension",
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
def _get_parser() -> CLIArgumentParser:
    parser = CLIArgumentParser(
        prog="ulauncher",  # override Python 3.14 argparse's `python3 -m ulauncher` auto-prog
        usage="%(prog)s [COMMAND] [OPTIONS]",
        description=CLI_DESCRIPTION,
        formatter_class=CLIHelpFormatter,
        version=f"Ulauncher {version}",
    )

    subparsers = parser.add_subparsers(
        parser_class=argparse.ArgumentParser,
        dest="command",
        # disable auto generated subparser help (we want to control how its rendered)
        help=argparse.SUPPRESS,
    )

    for command_name, command in _get_commands().items():
        command_parser = subparsers.add_parser(
            command_name,
            aliases=list(command.aliases),
            help=command.summary,
            description=command.description,
            formatter_class=CLIHelpFormatter,
        )
        for argument in command.arguments:
            command_parser.add_argument(*argument.args, **argument.kwargs)
        # Accept --verbose on every subparser so users don't have to remember which commands
        # use logging. Hidden (and warned-about post-parse) for commands that don't.
        verbose_help = "Use verbose logging" if command.has_runtime else argparse.SUPPRESS
        command_parser.add_argument("-v", "--verbose", action="store_true", help=verbose_help)
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
        configure_logging(verbose=args.verbose, use_app_logging=command.group == "App")
    elif args.verbose:
        _emit_warning(f"--verbose has no effect on the {args.command} command")
    return _load_handler(args.command)(args)


def _emit_warning(msg: str) -> None:
    if sys.stderr.isatty():
        msg = f"\033[33m{msg}\033[0m"
    sys.stderr.write(f"{msg}\n")


def parse(input_args: list[str]) -> CLIArguments:
    """Parse CLI arguments"""
    # --verbose/-v used to be a top-level argument, but is now subparser level.
    # Sorting it last for compatibility.
    args = sorted(input_args, key=lambda arg: arg in ("-v", "--verbose"))
    if all(arg in ("-v", "--verbose") for arg in args):
        args = ["show", *args]
    return CLIArguments(**vars(_get_parser().parse_args(args=args)))
