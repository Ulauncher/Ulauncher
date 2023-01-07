import logging
import os
from shutil import which
from gi.repository import GLib

logger = logging.getLogger()
use_systemd_run = which("systemd-run") and os.system("systemd-run --user --scope true  2> /dev/null") == 0

if not use_systemd_run:
    logger.warning(
        "Your system does not support launching applications in isolated scopes.\n"
        "This may result in applications launched by Ulauncher to depend on the main\n"
        "process (Ulauncher) and forced to exit prematurely if Ulauncher exits or crashes.\n"
        "Most likely this is caused by using an outdated or or misconfigured system.\n\n"
        "For more details see https://github.com/Ulauncher/Ulauncher/discussions/991"
    )


def launch_detached(cmd):
    if use_systemd_run:
        cmd = ["systemd-run", "--user", "--scope"] + cmd

    env = dict(os.environ.items())
    # Make sure GDK apps aren't forced to use x11 on wayland due to ulauncher's need to run
    # under X11 for proper centering.
    env.pop("GDK_BACKEND", None)

    try:
        envp = [f"{k}={v}" for k, v in env.items()]
        GLib.spawn_async(
            argv=cmd,
            envp=envp,
            flags=GLib.SpawnFlags.SEARCH_PATH_FROM_ENVP | GLib.SpawnFlags.SEARCH_PATH,
            child_setup=None if use_systemd_run else os.setsid,
        )
    except Exception as e:
        logger.error("%s: %s", type(e).__name__, e)
