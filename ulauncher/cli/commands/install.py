import asyncio
import logging

from ulauncher.cli import CLIArguments
from ulauncher.cli.commands import get_ext_controller, normalize_ext_arg
from ulauncher.cli.commands.upgrade import upgrade_one
from ulauncher.modes.extensions import ext_exceptions
from ulauncher.modes.extensions.extension_controller import ExtensionController
from ulauncher.utils.dbus import dbus_trigger_event

logger = logging.getLogger(__name__)


def run(args: CLIArguments) -> int:
    if controller := get_ext_controller(args.input):
        return 0 if upgrade_one(controller) else 1

    url = normalize_ext_arg(args.input)
    try:
        controller = asyncio.run(ExtensionController.install(url))
        dbus_trigger_event("extensions:reload", [controller.id])
    except (ValueError, ext_exceptions.UrlError):  # error already logged
        return 1
    except (ext_exceptions.NetworkError, ext_exceptions.RemoteError):
        logger.warning("Network error: Could not install %s", args.input)
        return 1
    return 0
