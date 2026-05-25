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
    # `install <path-or-url>` is idempotent by design: re-running on an already-installed
    # extension upgrades it. Lets `ulauncher i .` work as a one-command dev loop. See #1505.
    if controller := get_ext_controller(args.input):
        logger.info("Extension '%s' is already installed, checking for updates...", controller.id)
        return 0 if upgrade_one(controller) else 1

    url = normalize_ext_arg(args.input)
    try:
        controller = asyncio.run(ExtensionController.install(url))
        dbus_trigger_event("extensions:reload", [controller.id])
    except (ValueError, ext_exceptions.UrlError):  # error already logged
        return 1
    except (ext_exceptions.NetworkError, ext_exceptions.RemoteError):
        logger.error("Network error: Could not install %s", args.input)  # noqa: TRY400 - traceback is noise here
        return 1
    return 0
