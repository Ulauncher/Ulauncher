from __future__ import annotations

import logging
import os
import re
import shlex
from pathlib import Path

from ulauncher.gi import Gio, GioUnix, GLib
from ulauncher.modes.apps.try_raise_app import try_raise_app
from ulauncher.utils.launch_detached import launch_detached
from ulauncher.utils.settings import Settings

logger = logging.getLogger(__name__)


def _get_action_exec(action_name: str, desktop_entry_path: str | None) -> str | None:
    if not desktop_entry_path:
        return None
    keyfile = GLib.KeyFile()
    try:
        keyfile.load_from_file(desktop_entry_path, GLib.KeyFileFlags.NONE)
        return keyfile.get_string(f"Desktop Action {action_name}", "Exec")
    except GLib.Error:
        return None


def _get_exec(app: GioUnix.DesktopAppInfo, action_name: str | None = None) -> str | None:
    """Return the launch command for the app, or one of its actions, with field codes resolved."""
    desktop_entry_path = app.get_filename()
    exec_line = _get_action_exec(action_name, desktop_entry_path) if action_name else app.get_commandline()
    if not exec_line:
        return None
    if desktop_entry_path:
        exec_line = exec_line.replace("%k", desktop_entry_path)
    # strip field codes %f, %F, %u, %U, etc
    return re.sub(r"\%[uUfFdDnNickvm]", "", exec_line).strip()


def _load_app(desktop_entry_name: str) -> GioUnix.DesktopAppInfo | None:
    app = GioUnix.DesktopAppInfo.new(desktop_entry_name)
    if not app:
        logger.error("Could not load app %s", desktop_entry_name)
    return app


def launch_app(desktop_entry_name: str, action_name: str | None = None) -> bool:
    app_id = Path(desktop_entry_name).stem if desktop_entry_name.endswith(".desktop") else desktop_entry_name
    settings = Settings.load()
    app = _load_app(desktop_entry_name)
    if not app:
        return False

    is_dbus = app.get_boolean("DBusActivatable")
    is_terminal = app.get_boolean("Terminal")
    use_custom_terminal = is_terminal and bool(settings.terminal_command)
    app_exec = _get_exec(app, action_name)

    if action_name is not None and (is_dbus or not app_exec or (is_terminal and not use_custom_terminal)):
        # for actions where we have no command to spawn, let Gio invoke the action
        launch_context = Gio.AppLaunchContext()
        if os.environ.get("GDK_BACKEND") != "wayland":
            launch_context.unsetenv("GDK_BACKEND")
        app.launch_action(action_name, launch_context)
        return True
    if not app_exec:
        logger.error("Could not get Exec for app %s", app_id)
        return False

    if action_name is None and (settings.raise_if_started or app.get_boolean("SingleMainWindow")):
        app_wm_id = (app.get_string("StartupWMClass") or Path(app_exec).name).lower()
        if try_raise_app(app_wm_id):
            return True

    try:
        if is_dbus:  # an action with DBus activation already returned above
            # https://wiki.gnome.org/HowDoI/DBusApplicationLaunching
            cmd = ["gapplication", "launch", app_id]
        elif use_custom_terminal:
            cmd = [*shlex.split(settings.terminal_command), app_exec]
        elif is_terminal:  # a terminal action without a preferred terminal already returned above
            cmd = ["gtk-launch", app_id]
        else:
            cmd = shlex.split(app_exec)
    except ValueError:
        logger.exception("Could not parse command for app %s: %r", app_id, app_exec)
        return False

    logger.info("Run %s (%s) Exec %s", f"action {action_name}" if action_name else "application", app_id, cmd)
    launch_detached(cmd, app.get_string("Path"))
    return True
