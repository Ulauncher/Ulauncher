import asyncio
import logging

from ulauncher.cli import CLIArguments
from ulauncher.cli.commands import get_ext_controller
from ulauncher.utils.dbus import dbus_trigger_event

logger = logging.getLogger(__name__)


def run(args: CLIArguments) -> int:
    if controller := get_ext_controller(args.input):
        asyncio.run(controller.remove())
        dbus_trigger_event("extensions:stop", [controller.id])
        return 0

    logger.error("Error: Argument '%s' does not match any installed extension", args.input)
    return 1
