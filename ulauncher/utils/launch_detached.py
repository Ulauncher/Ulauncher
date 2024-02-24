import logging
import os

from gi.repository import GLib

from ulauncher.utils.systemd_controller import SystemdController

logger = logging.getLogger()


def launch_detached(cmd):
    cmd = (
        ["systemd-run", "--user", "--scope", *cmd]
        if SystemdController("ulauncher").is_active()
        else ["setsid", "nohup", *cmd]
    )

    env = dict(os.environ.items())
    # Make sure GDK apps aren't forced to use x11 on wayland due to ulauncher's need to run
    # under X11 for proper centering.
    if env.get("GDK_BACKEND") != "wayland":
        env.pop("GDK_BACKEND", None)

    try:
        envp = [f"{k}={v}" for k, v in env.items()]
        GLib.spawn_async(
            argv=cmd,
            envp=envp,
            flags=GLib.SpawnFlags.SEARCH_PATH_FROM_ENVP | GLib.SpawnFlags.SEARCH_PATH,
            standard_output=True,
            standard_error=True,
        )
    except Exception:
        logger.exception('Could not launch "%s"', cmd)


def open_detached(path_or_url):
    launch_detached(["xdg-open", path_or_url])
