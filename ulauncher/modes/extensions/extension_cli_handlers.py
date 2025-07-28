import asyncio
import logging
from argparse import ArgumentParser, Namespace
from pathlib import Path

logger = logging.getLogger(__name__)

# Import other modules within functions to avoid circular deps and make sure the logger is initialized


def list_active_extensions(_: ArgumentParser, __: Namespace) -> bool:
    from ulauncher.modes.extensions.extension_controller import ExtensionController

    for controller in ExtensionController.iterate():
        disabled_label = " [DISABLED]" if not controller.is_enabled else ""
        logger.info("- %s (%s)%s", controller.manifest.name, controller.id, disabled_label)
    if not ExtensionController.iterate():
        logger.info("No extensions installed.")

    return True


def install_extension(parser: ArgumentParser, args: Namespace) -> bool:
    if "input" not in args or not args.input:
        logger.error("Error: URL or path is required for installing an extension")
        parser.print_help()
        return False

    from ulauncher.modes.extensions.extension_controller import ExtensionController

    try:
        url = args.input
        if not url.startswith(("http", "git@")):
            # It's a local path. Verify it exists and make absolute path
            path = Path(url).resolve()
            if not path.exists():
                logger.error("Error: The specified path '%s' does not exist", path)
                return False
            url = str(path)

        controller = ExtensionController.create_from_url(url)
        asyncio.run(controller.install())
    except Exception:
        logger.exception("Failed to install extension")
        return False

    return True


def uninstall_extension(parser: ArgumentParser, args: Namespace) -> bool:
    if "input" not in args or not args.input:
        logger.error("Error: ID or URL is required for uninstalling an extension")
        parser.print_help()
        return False

    from ulauncher.modes.extensions.extension_controller import ExtensionController, ExtensionNotFoundError

    # Handle both extension ID and URL
    try:
        controller = (
            ExtensionController.create_from_url(args.input)
            if args.input.startswith(("http", "git@"))
            else ExtensionController.create(args.input)
        )
    except Exception:
        logger.exception("Failed to find extension controller for '%s'", args.input)
        return False

    try:
        asyncio.run(controller.remove())
    except ExtensionNotFoundError:
        logger.warning("Extension '%s' is not installed", args.input)
        return False
    except Exception:
        logger.exception("Failed to uninstall extension '%s'", args.input)
        return False

    return True


def upgrade_extensions(_: ArgumentParser, args: Namespace) -> bool:
    from ulauncher.modes.extensions.extension_controller import ExtensionController, ExtensionNotFoundError

    if "input" in args and args.input:
        # Upgrade specific extension
        try:
            controller = (
                ExtensionController.create_from_url(args.input)
                if args.input.startswith(("http", "git@"))
                else ExtensionController.create(args.input)
            )
            asyncio.run(controller.update())
        except ExtensionNotFoundError:
            logger.warning("Extension '%s' is not installed", args.input)
            return False
        except Exception:
            logger.exception("Failed to upgrade extension %s", args.input)
            return False

        return True

    updated_count = 0

    for controller in ExtensionController.iterate():
        if not controller.is_manageable or not controller.state.url:
            continue

        try:
            ext_name = controller.manifest.name
            updated = asyncio.run(controller.update())
            if updated:
                updated_count += 1
        except Exception:
            logger.exception("Failed to update %s", ext_name)

    if updated_count == 0:
        logger.info("All extensions are up to date")
    else:
        logger.info("Successfully updated %s extensions", updated_count)

    return True
