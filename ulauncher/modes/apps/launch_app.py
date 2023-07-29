import logging
import re
import shlex
from pathlib import Path

from gi.repository import Gio

from ulauncher.utils.environment import IS_X11
from ulauncher.utils.launch_detached import launch_detached
from ulauncher.utils.Settings import Settings
from ulauncher.utils.wm import get_windows_stacked, get_xserver_time

logger = logging.getLogger()


def launch_app(desktop_entry_name):
    app_id = Path(desktop_entry_name).stem if desktop_entry_name.endswith(".desktop") else desktop_entry_name
    settings = Settings.load()
    app = Gio.DesktopAppInfo.new(desktop_entry_name)
    # strip field codes %f, %F, %u, %U, etc
    app_exec = re.sub(r"\%[uUfFdDnNickvm]", "", app.get_commandline()).strip()
    app_wm_id = (app.get_string("StartupWMClass") or Path(app_exec).name).lower()
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
        cmd = ["gapplication", "launch", app_id]
    elif app_exec:
        if app.get_boolean("Terminal"):
            terminal_exec = settings.terminal_command
            if terminal_exec:
                logger.info("Will run command in preferred terminal (%s)", terminal_exec)
                cmd = [*shlex.split(terminal_exec), app_exec]
            else:
                cmd = ["gtk-launch", app_id]
        else:
            cmd = shlex.split(app_exec)

    if not cmd:
        logger.error("No command to run %s", app_id)
    else:
        logger.info("Run application %s (%s) Exec %s", app.get_name(), app_id, cmd)
        launch_detached(cmd)
