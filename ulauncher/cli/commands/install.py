from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from ulauncher.cli.commands import get_ext_controller, normalize_ext_arg
from ulauncher.modes.extensions import ext_exceptions
from ulauncher.utils.dbus import dbus_trigger_event

if TYPE_CHECKING:
    from ulauncher.cli import CLIArguments

logger = logging.getLogger(__name__)


def run(args: CLIArguments) -> bool:
    from ulauncher.modes.extensions.extension_controller import ExtensionController

    if get_ext_controller(args.input):
        from ulauncher.cli.commands.upgrade import run as run_upgrade

        return run_upgrade(args)

    url = normalize_ext_arg(args.input)
    try:
        controller = asyncio.run(ExtensionController.install(url))
        dbus_trigger_event("extensions:reload", [controller.id])
    except (ValueError, ext_exceptions.UrlError):  # error already logged
        return False
    except ext_exceptions.RemoteError:
        logger.warning("Network error: Could not install %s", args.input)
        return False
    return True
