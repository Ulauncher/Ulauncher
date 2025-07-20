from __future__ import annotations

import logging
import os
import re
import shlex
from pathlib import Path

from gi.repository import Gio

from ulauncher.utils.launch_detached import launch_detached
from ulauncher.utils.settings import Settings
from ulauncher.utils.wm import try_raise_app

logger = logging.getLogger()


def launch_app(desktop_entry_name: str) -> bool:
    app_id = Path(desktop_entry_name).stem if desktop_entry_name.endswith(".desktop") else desktop_entry_name
    settings = Settings.load()
    app = Gio.DesktopAppInfo.new(desktop_entry_name)
    app_dir: str | None = None
    if not app:
        logger.error("Could not load app %s", desktop_entry_name)
        return False

    app_exec = app.get_commandline()
    if not app_exec:
        logger.error("Could not get Exec for app %s", app_id)
        return False

    if desktop_entry_path := app.get_filename():
        app_exec = app_exec.replace("%k", desktop_entry_path)
        app_dir = os.path.dirname(desktop_entry_path)

    # strip field codes %f, %F, %u, %U, etc
    app_exec = re.sub(r"\%[uUfFdDnNickvm]", "", app_exec).strip()
    app_wm_id = (app.get_string("StartupWMClass") or Path(app_exec).name).lower()
    prefer_raise = settings.raise_if_started or app.get_boolean("SingleMainWindow")
    if prefer_raise and app_exec and try_raise_app(app_wm_id):
        return True

    if app.get_boolean("DBusActivatable"):
        # https://wiki.gnome.org/HowDoI/DBusApplicationLaunching
        cmd = ["gapplication", "launch", app_id]
    elif app_exec:
        if app.get_boolean("Terminal"):
            if terminal_exec := settings.terminal_command:
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
        working_dir = app.get_string("Path") or app_dir
        launch_detached(cmd, working_dir)
    return True
