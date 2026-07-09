import logging

from ulauncher.cli import CLIArguments
from ulauncher.cli.commands import get_ext_record, get_ext_registry

logger = logging.getLogger(__name__)


def run(args: CLIArguments) -> int:
    if record := get_ext_record(args.input):
        if not record.is_manageable:
            logger.error("Extension %s is externally managed and can not be uninstalled (%s)", record.id, record.path)
            return 1
        try:
            get_ext_registry().uninstall(record)
        except OSError:
            logger.error("Could not uninstall %s", record.id)  # noqa: TRY400 - traceback is noise here
            return 1
        return 0

    logger.error("Error: Argument '%s' does not match any installed extension", args.input)
    return 1
