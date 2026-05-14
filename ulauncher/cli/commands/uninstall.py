from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from ulauncher.cli.commands import get_ext_controller
from ulauncher.utils.dbus import dbus_trigger_event

if TYPE_CHECKING:
    from ulauncher.cli import CLIArguments

logger = logging.getLogger(__name__)


def run(args: CLIArguments) -> int:
    if controller := get_ext_controller(args.input):
        asyncio.run(controller.remove())
        dbus_trigger_event("extensions:stop", [controller.id])
        return 0

    logger.error("Error: Argument '%s' does not match any installed extension", args.input)
    return 1
