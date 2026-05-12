from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ulauncher.cli import CLIArguments

logger = logging.getLogger(__name__)


def run(_: CLIArguments) -> bool:
    from ulauncher.modes.extensions import extension_registry

    extensions = list(extension_registry.load_all())
    for controller in extensions:
        disabled_label = " [DISABLED]" if not controller.is_enabled else ""
        logger.info("- %s (%s)%s", controller.manifest.name, controller.id, disabled_label)
    if not extensions:
        logger.info("No extensions installed.")

    return True
