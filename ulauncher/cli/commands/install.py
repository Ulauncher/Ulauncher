import logging

from ulauncher.cli import CLIArguments
from ulauncher.cli.commands import get_ext_registry, normalize_ext_arg
from ulauncher.modes.extensions import ext_exceptions

logger = logging.getLogger(__name__)


def run(args: CLIArguments) -> int:
    # registry.install is idempotent and will also upgrade to latest (if installed) or shadow non-manageable.
    url = normalize_ext_arg(args.input)
    try:
        get_ext_registry().install(url)
    except (ValueError, ext_exceptions.UrlError):  # error already logged
        return 1
    except (ext_exceptions.NetworkError, ext_exceptions.RemoteError):
        logger.error("Network error: Could not install %s", args.input)  # noqa: TRY400 - traceback is noise here
        return 1
    except (ext_exceptions.ExtensionError, OSError) as e:
        logger.error("Could not install %s: %s", args.input, e)  # noqa: TRY400 - traceback is noise here
        return 1
    return 0
