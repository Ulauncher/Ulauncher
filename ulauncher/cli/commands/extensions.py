import logging

from ulauncher.cli import CLIArguments
from ulauncher.cli.commands import get_ext_registry

logger = logging.getLogger(__name__)


def run(_: CLIArguments) -> int:
    extensions = list(get_ext_registry().iterate(sort=True))
    for ext in extensions:
        disabled_label = " [DISABLED]" if not ext.is_enabled else ""
        logger.info("- %s (%s)%s", ext.manifest.name, ext.id, disabled_label)
    if not extensions:
        logger.info("No extensions installed.")

    return 0
