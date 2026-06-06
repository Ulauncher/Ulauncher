import logging

from ulauncher.cli import CLIArguments
from ulauncher.modes.extensions import extension_registry

logger = logging.getLogger(__name__)


def run(_: CLIArguments) -> int:
    extensions = extension_registry.load_all()
    for controller in extensions:
        disabled_label = " [DISABLED]" if not controller.is_enabled else ""
        logger.info("- %s (%s)%s", controller.manifest.name, controller.id, disabled_label)
    if not extensions:
        logger.info("No extensions installed.")

    return 0
