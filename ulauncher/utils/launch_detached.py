import logging
import os
from shutil import which
import gi

gi.require_version("GLib", "2.0")
# pylint: disable=wrong-import-position
from gi.repository import GLib

logger = logging.getLogger(__name__)
has_systemd = which("systemctl") and which("systemd-run")
runs_in_systemd = has_systemd and os.system('systemctl --user is-active --quiet ulauncher') == 0


def launch_detached(cmd):
    if runs_in_systemd:
        logger.warning(
            "Will attempt to launch the app using systemd-run with --scope argument"
            "This prevents the apps from terminating if Ulauncher crashes or is restarted."
            "On some systems with outdated systemd or incorrect permissions this doesn't work."
            "If this happens to you, don't run Ulauncher from systemd."
        )
        cmd = ['systemd-run', '--user', '--scope'] + cmd

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
            # setsid is really only needed if systemd-run is missing, but doesn't hurt to have.
            child_setup=os.setsid
        )
    except Exception as e:
        logger.error('%s: %s', type(e).__name__, e)
