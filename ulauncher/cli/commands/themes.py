import logging

from ulauncher.cli import CLIArguments
from ulauncher.internals import theme_installer

logger = logging.getLogger(__name__)


def run(_: CLIArguments) -> int:
    repo_ids = theme_installer.installed_ids()
    for repo_id in repo_ids:
        state = theme_installer.load_state(repo_id)
        logger.info("- %s (%s)", repo_id, state.url or "unknown source")
    if not repo_ids:
        logger.info("No themes installed.")

    return 0
