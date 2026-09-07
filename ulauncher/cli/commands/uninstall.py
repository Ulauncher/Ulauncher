import logging

from ulauncher.cli import CLIArguments
from ulauncher.cli.commands import get_ext_record, get_ext_registry, get_theme_id, run_blocking
from ulauncher.internals import theme_installer
from ulauncher.utils.dbus import dbus_trigger_event

logger = logging.getLogger(__name__)


def run(args: CLIArguments) -> int:
    # An id can exist in both stores when a repo changed kind upstream and was
    # reinstalled. Handle both so a single uninstall does not leave one behind.
    record = get_ext_record(args.input)
    theme_id = get_theme_id(args.input)
    if not record and not theme_id:
        logger.error("Error: Argument '%s' does not match any installed extension or theme", args.input)
        return 1

    exit_code = 0
    if record:
        if not record.is_manageable:
            logger.error("Extension %s is externally managed and can not be uninstalled (%s)", record.id, record.path)
            exit_code = 1
        else:
            registry = get_ext_registry()
            try:
                run_blocking(lambda done, fail: registry.uninstall(record, lambda: done(None), fail))
            except OSError:
                logger.error("Could not uninstall %s", record.id)  # noqa: TRY400 - traceback is noise here
                exit_code = 1
            else:
                dbus_trigger_event("extensions:reload", [record.id])

    if theme_id:
        try:
            theme_installer.uninstall(theme_id)
        except OSError:
            logger.error("Could not uninstall %s", theme_id)  # noqa: TRY400 - traceback is noise here
            exit_code = 1
        else:
            dbus_trigger_event("themes:reload")
            logger.info("Theme %s uninstalled", theme_id)
    return exit_code
