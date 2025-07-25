import asyncio
from argparse import ArgumentParser, Namespace

# Import other modules within functions to avoid circular deps and make sure the logger is initialized


def list_active_extensions(_: ArgumentParser, __: Namespace) -> bool:
    import logging

    from ulauncher.modes.extensions.extension_controller import ExtensionController

    logger = logging.getLogger(__name__)

    for controller in ExtensionController.iterate():
        disabled_label = " [DISABLED]" if not controller.is_enabled else ""
        logger.info("- %s (%s)%s", controller.manifest.name, controller.id, disabled_label)
    if not ExtensionController.iterate():
        logger.info("No extensions installed.")

    return True


def install_extension(parser: ArgumentParser, args: Namespace) -> bool:
    import logging

    logger = logging.getLogger(__name__)

    if "URL" not in args or not args.URL:
        logger.error("Error: URL is required for installing an extension")
        parser.print_help()
        return False

    from ulauncher.modes.extensions.extension_controller import ExtensionController

    try:
        controller = ExtensionController.create_from_url(args.URL)
        asyncio.run(controller.install())
    except Exception:
        logger.exception("Failed to install extension")
        return False

    return True


def uninstall_extension(parser: ArgumentParser, args: Namespace) -> bool:
    import logging

    logger = logging.getLogger(__name__)

    if "ID_OR_URL" not in args or not args.ID_OR_URL:
        logger.error("Error: ID or URL is required for installing an extension")
        parser.print_help()
        return False

    id_or_url = args.ID_OR_URL

    from ulauncher.modes.extensions.extension_controller import ExtensionController, ExtensionNotFoundError

    # Handle both extension ID and URL
    try:
        controller = (
            ExtensionController.create_from_url(id_or_url)
            if id_or_url.startswith(("http", "git@"))
            else ExtensionController.create(id_or_url)
        )
    except Exception:
        logger.exception("Failed to find extension controller for '%s'", id_or_url)
        return False

    try:
        asyncio.run(controller.remove())
    except ExtensionNotFoundError:
        logger.warning("Extension '%s' is not installed", id_or_url)
        return False
    except Exception:
        logger.exception("Failed to uninstall extension '%s'", id_or_url)
        return False

    return True


def upgrade_extensions(_: ArgumentParser, args: Namespace) -> bool:
    import logging

    logger = logging.getLogger(__name__)
    from ulauncher.modes.extensions.extension_controller import ExtensionController, ExtensionNotFoundError

    if "ID_OR_URL" in args and args.ID_OR_URL:
        id_or_url = args.ID_OR_URL
        # Upgrade specific extension
        try:
            controller = (
                ExtensionController.create_from_url(id_or_url)
                if id_or_url.startswith(("http", "git@"))
                else ExtensionController.create(id_or_url)
            )
            asyncio.run(controller.update())
        except ExtensionNotFoundError:
            logger.warning("Extension '%s' is not installed", id_or_url)
            return False
        except Exception:
            logger.exception("Failed to upgrade extension %s", id_or_url)
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
