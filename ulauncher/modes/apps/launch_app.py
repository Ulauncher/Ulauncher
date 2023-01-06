import logging
import re
import shlex
from os.path import basename
from gi.repository import Gio
from ulauncher.utils.environment import IS_X11
from ulauncher.utils.Settings import Settings
from ulauncher.utils.launch_detached import launch_detached
from ulauncher.utils.wm import get_windows_stacked, get_xserver_time

logger = logging.getLogger()


def launch_app(app_id):
    settings = Settings.load()
    app = Gio.DesktopAppInfo.new(app_id)
    # strip field codes %f, %F, %u, %U, etc
    app_exec = re.sub(r"\%[uUfFdDnNickvm]", "", app.get_commandline()).strip()
    app_wm_id = (app.get_string("StartupWMClass") or basename(app_exec)).lower()
    if app_exec and IS_X11 and (settings.raise_if_started or app.get_boolean("SingleMainWindow")):
        for win in get_windows_stacked():
            win_app_wm_id = (win.get_class_group_name() or "").lower()
            if win_app_wm_id == "thunar" and win.get_name().startswith("Bulk Rename"):
                # "Bulk Rename" identify as "Thunar": https://gitlab.xfce.org/xfce/thunar/-/issues/731
                win_app_wm_id = "thunar --bulk-rename"
            if win_app_wm_id == app_wm_id:
                logger.info("Raising application %s", app_wm_id)
                win.activate(get_xserver_time())
                return

    if app.get_boolean("DBusActivatable"):
        # https://wiki.gnome.org/HowDoI/DBusApplicationLaunching
        exec = ["gapplication", "launch", app_id.replace(".desktop", "")]
    elif app_exec:
        if app.get_boolean("Terminal"):
            terminal_exec = settings.terminal_command
            if terminal_exec:
                logger.info("Will run command in preferred terminal (%s)", terminal_exec)
                exec = shlex.split(terminal_exec) + [app_exec]
            else:
                exec = ["gtk-launch", app_id]
        else:
            exec = shlex.split(app_exec)

    if not exec:
        logger.error("No command to run %s", app_id)
    else:
        logger.info("Run application %s (%s) Exec %s", app.get_name(), app_id, exec)
        launch_detached(exec)
