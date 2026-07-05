import asyncio
import logging

from ulauncher.cli import CLIArguments
from ulauncher.cli.commands import get_ext_record, get_ext_registry
from ulauncher.utils.dbus import dbus_trigger_event

logger = logging.getLogger(__name__)


def run(args: CLIArguments) -> int:
    if record := get_ext_record(args.input):
        asyncio.run(get_ext_registry().uninstall(record))
        dbus_trigger_event("extensions:stop", [record.id])
        return 0

    logger.error("Error: Argument '%s' does not match any installed extension", args.input)
    return 1
